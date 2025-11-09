import pandas as pd
import re
import os
import altair as alt
import numpy as np
from datetime import datetime

# --- Helper Functions ---

def clean_data(df):
    """Cleans 'Amount' and 'Count' columns in a DataFrame."""
    if 'Amount' in df.columns:
        df['Amount'] = df['Amount'].astype(str).str.replace(r'[$,]', '', regex=True)
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    
    if 'Count' in df.columns:
        df['Count'] = df['Count'].astype(str).str.replace(',', '', regex=True)
        df['Count'] = pd.to_numeric(df['Count'], errors='coerce')
    
    return df

# --- Inventory Analysis Function ---

def get_inventory_analysis(data_dir, all_items_df):
    """
    Analyzes sales data against ingredient recipes and shipments
    to predict inventory status.
    """
    
    # --- 1. Load Ingredient & Shipment Files (as CSVs) ---
    ingredient_file = os.path.join(data_dir, "MSY Data - Ingredient.csv")
    shipment_file = os.path.join(data_dir, "MSY Data - Shipment.csv")
    
    try:
        recipe_df = pd.read_csv(ingredient_file)
        print("[SUCCESS] Processed: MSY Data - Ingredient.csv")
    except Exception as e:
        print(f"[ERROR] Could not read {ingredient_file}: {e}")
        return "{}", "{}", []

    try:
        shipment_df = pd.read_csv(shipment_file)
        print("[SUCCESS] Processed: MSY Data - Shipment.csv")
    except Exception as e:
        print(f"[ERROR] Could not read {shipment_file}: {e}")
        return "{}", "{}", []

    # --- 2. Calculate Total Item Sales (6 Months) ---
    total_sales_df = all_items_df.groupby('Item Name')['Count'].sum().reset_index()
    total_sales_df = total_sales_df.rename(columns={'Count': 'Total_6_Month_Sales'})

    # --- 3. Parse Ingredient Units & Clean Headers ---
    ingredient_units = {}
    new_columns = {}
    unit_pattern = re.compile(r'\s?\((g|pcs|count)\)')
    
    for col in recipe_df.columns:
        match = unit_pattern.search(col)
        if match:
            unit = match.group(1)
            clean_name = unit_pattern.sub('', col)
            ingredient_units[clean_name] = unit
            new_columns[col] = clean_name
        else:
            ingredient_units[col] = 'g' 
            new_columns[col] = col
            
    recipe_df = recipe_df.rename(columns=new_columns)
    recipe_df = recipe_df.rename(columns={'Item name': 'Item Name'})
    ingredient_units['Item Name'] = 'text'
    
    recipe_df = recipe_df.set_index('Item Name').fillna(0)

    # --- 4. Combine Chicken Units ---
    recipe_df['Total_Chicken_Usage'] = recipe_df['Braised Chicken'] + (recipe_df['chicken thigh'] * 100)
    ingredient_units['Total_Chicken_Usage'] = 'g'
    recipe_df = recipe_df.drop(columns=['Braised Chicken', 'chicken thigh'])

    # --- 5. Calculate Total Ingredient Usage (6 Months) ---
    usage_df = total_sales_df.merge(recipe_df, left_on='Item Name', right_index=True, how='inner')
    
    ingredient_columns = recipe_df.columns
    total_usage = {}
    for col in ingredient_columns:
        total_usage[col] = (usage_df[col] * usage_df['Total_6_Month_Sales']).sum()
    
    total_usage_df = pd.DataFrame.from_dict(total_usage, orient='index', columns=['Total_6_Month_Usage'])
    total_usage_df['Avg_Monthly_Usage'] = total_usage_df['Total_6_Month_Usage'] / 6
    total_usage_df.index.name = 'Ingredient_Recipe_Name'
    
    # --- 6. Calculate Monthly Shipment Volume & Normalize Units ---
    
    def normalize_frequency(freq):
        freq = str(freq).lower()
        if 'weekly' in freq: return 4
        if 'biweekly' in freq: return 2
        if 'monthly' in freq: return 1
        return 0

    shipment_df['Shipments_Per_Month'] = shipment_df['frequency'].apply(normalize_frequency)
    shipment_df['Total_Shipped_Per_Month'] = shipment_df['Quantity per shipment'] * shipment_df['Number of shipments'] * shipment_df['Shipments_Per_Month']
    
    unit_conversions = {
        'lbs': 453.592, 'rolls': 1, 'pieces': 1, 'eggs': 1, 'whole onion': 150
    }
    
    shipment_df['Conversion_Factor'] = shipment_df['Unit of shipment'].map(unit_conversions).fillna(1)
    shipment_df['Total_Shipped_Per_Month_Converted'] = shipment_df['Total_Shipped_Per_Month'] * shipment_df['Conversion_Factor']
    
    # --- 7. Map Shipment Ingredients to Recipe Ingredients ---
    ingredient_map = {
        'Beef': 'braised beef used',
        'Chicken': 'Total_Chicken_Usage',
        'Ramen': 'Ramen',
        'Rice Noodles': 'Rice Noodles',
        'Flour': 'flour',
        'Tapioca Starch': 'Tapioca Starch',
        'Rice': 'Rice',
        'Green Onion': 'Green Onion',
        'White Onion': 'White onion',
        'Cilantro': 'Cilantro',
        'Egg': 'Egg',
        'Peas + Carrot': 'Peas',
        'Bokchoy': 'Boychoy',
        'Chicken Wings': 'Chicken Wings'
    }
    
    shipment_df_final = shipment_df.set_index('Ingredient')
    analysis_data = []
    
    for shipment_name, recipe_name in ingredient_map.items():
        if shipment_name in shipment_df_final.index and recipe_name in total_usage_df.index:
            monthly_usage = total_usage_df.loc[recipe_name, 'Avg_Monthly_Usage']
            monthly_shipment = shipment_df_final.loc[shipment_name, 'Total_Shipped_Per_Month_Converted']
            unit = ingredient_units.get(recipe_name, 'g')

            if shipment_name == 'Peas + Carrot':
                peas_usage = total_usage_df.loc['Peas', 'Avg_Monthly_Usage']
                carrot_usage = total_usage_df.loc['Carrot', 'Avg_Monthly_Usage']
                total_usage_pc = peas_usage + carrot_usage
                delta = monthly_shipment - total_usage_pc
                analysis_data.append({'Ingredient': 'Peas & Carrot', 'Unit': 'g', 'Avg_Monthly_Usage': total_usage_pc, 'Monthly_Shipment': monthly_shipment, 'Stock_Delta': delta})
            else:
                delta = monthly_shipment - monthly_usage
                analysis_data.append({'Ingredient': shipment_name, 'Unit': unit, 'Avg_Monthly_Usage': monthly_usage, 'Monthly_Shipment': monthly_shipment, 'Stock_Delta': delta})

    analysis_df = pd.DataFrame(analysis_data)
    
    if analysis_df.empty:
        return "{}", {}, []

    # --- 8. Format for Dashboard ---
    
    def assign_status(row):
        avg_monthly_usage = row['Avg_Monthly_Usage']
        stock_delta = row['Stock_Delta']
        
        status = 'Stocked'
        note = 'Buffer is 1-6 weeks'
        
        if avg_monthly_usage <= 0:
            if stock_delta > 0:
                status = 'Surplus'
                note = 'Stocked but not sold'
            else:
                status = 'Stocked'
                note = 'No sales data'
            return status, note

        safety_stock_buffer = avg_monthly_usage * 0.25
        surplus_buffer = avg_monthly_usage * 1.5

        if stock_delta < safety_stock_buffer:
            status = 'Low Stock'
            note = 'Buffer is < 1 week of usage'
        elif stock_delta > surplus_buffer:
            status = 'Surplus'
            note = 'Buffer is > 6 weeks of usage'

        return status, note

    analysis_df[['Status', 'Note']] = analysis_df.apply(assign_status, axis=1, result_type='expand')
    analysis_df = analysis_df.round(0)
    
    # --- NEW: Generate Low Stock Alerts ---
    low_stock_alerts = []
    low_stock_items = analysis_df[analysis_df['Status'] == 'Low Stock']
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    for idx, row in low_stock_items.iterrows():
        alert = {
            'date': current_date,
            'ingredient': row['Ingredient'],
            'message': f"Low stock alert: {row['Ingredient']} buffer is less than 1 week of usage",
            'icon': 'fa-exclamation-triangle',
            'color': 'warning'
        }
        low_stock_alerts.append(alert)
    
    # --- Table: Inventory Status ---
    inventory_table_data = analysis_df.to_json(orient='records')

    # --- Chart: Data for Chart.js ---
    analysis_df = analysis_df.sort_values(by='Stock_Delta')
    
    def assign_chart_color(status):
        if status == 'Low Stock':
            return 'rgba(231, 74, 59, 0.8)'
        elif status == 'Surplus':
            return 'rgba(246, 194, 62, 0.8)'
        else:
            return 'rgba(28, 200, 138, 0.8)'

    def assign_border_color(status):
        if status == 'Low Stock':
            return 'rgba(231, 74, 59, 1)'
        elif status == 'Surplus':
            return 'rgba(246, 194, 62, 1)'
        else:
            return 'rgba(28, 200, 138, 1)'

    analysis_df['Color'] = analysis_df['Status'].apply(assign_chart_color)
    analysis_df['BorderColor'] = analysis_df['Status'].apply(assign_border_color)

    inventory_chart_data = {
        'labels': analysis_df['Ingredient'].tolist(),
        'data': analysis_df['Stock_Delta'].tolist(),
        'colors': analysis_df['Color'].tolist(),
        'borderColors': analysis_df['BorderColor'].tolist(),
        'units': analysis_df['Unit'].tolist()
    }
    
    return inventory_table_data, inventory_chart_data, low_stock_alerts

# --- Main Data Analysis Function ---

def get_dashboard_data():
    """
    Reads all XLSX files from the data/ folder and returns key metrics
    for the Flask dashboard.
    """
    base_dir = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(base_dir, 'data')

    print("--- Dashboard Analysis (XLSX Mode) ---")
    print(f"Looking for data files in: {data_dir}")
    print("--------------------------------------")

    # --- 1. Monthly Revenue Analysis (data 1) ---
    group_files = {
        "May":       {"file": "May_Data_Matrix.xlsx", "sheet": "data 1"},
        "June":      {"file": "June_Data_Matrix.xlsx", "sheet": "data 1"},
        "July":      {"file": "July_Data_Matrix.xlsx", "sheet": "data 1"},
        "August":    {"file": "August_Data_Matrix.xlsx", "sheet": "data 1"},
        "September": {"file": "September_Data_Matrix.xlsx", "sheet": "data 1"},
        "October":   {"file": "October_Data_Matrix_20251103_214000.xlsx", "sheet": "data 3"}
    }
    monthly_revenue = []
    for month, info in group_files.items():
        full_path = os.path.join(data_dir, info['file'])
        sheet_name = info['sheet']
        if not os.path.exists(full_path):
            print(f"[ERROR] File NOT FOUND: {full_path}")
            continue
        try:
            df = pd.read_excel(full_path, sheet_name=sheet_name)
            df = clean_data(df)
            total_revenue = df['Amount'].sum()
            monthly_revenue.append({"Month": month, "Total_Revenue": total_revenue})
            print(f"[SUCCESS] Processed: {info['file']} (Sheet: {sheet_name})")
        except Exception as e:
            print(f"[ERROR] Failed to process {full_path} (Sheet: {sheet_name}): {e}")
    if not monthly_revenue:
        raise FileNotFoundError(f"No 'Group' data was loaded. Check files in '{data_dir}'.")
    revenue_df = pd.DataFrame(monthly_revenue)
    month_order = ["May", "June", "July", "August", "September", "October"]
    revenue_df['Month'] = pd.Categorical(revenue_df['Month'], categories=month_order, ordered=True)
    revenue_df = revenue_df.sort_values('Month')

    # --- 2. Top Items Analysis (data 3) ---
    item_files = {
        "May":       {"file": "May_Data_Matrix.xlsx", "sheet": "data 3"},
        "June":      {"file": "June_Data_Matrix.xlsx", "sheet": "data 3"},
        "July":      {"file": "July_Data_Matrix.xlsx", "sheet": "data 3"},
        "August":    {"file": "August_Data_Matrix.xlsx", "sheet": "data 3"},
        "September": {"file": "September_Data_Matrix.xlsx", "sheet": "data 3"},
        "October":   {"file": "October_Data_Matrix_20251103_214000.xlsx", "sheet": "data 3"} 
    }
    all_items = []
    for month, info in item_files.items():
        full_path = os.path.join(data_dir, info['file'])
        sheet_name = info['sheet']
        if not os.path.exists(full_path):
            print(f"[ERROR] File NOT FOUND: {full_path}")
            continue
        try:
            df = pd.read_excel(full_path, sheet_name=sheet_name)
            df = clean_data(df)
            df['Month'] = month
            all_items.append(df)
            print(f"[SUCCESS] Processed: {info['file']} (Sheet: {sheet_name})")
        except Exception as e:
            print(f"[ERROR] Failed to process item file {full_path} (Sheet: {sheet_name}): {e}")
    if not all_items:
        raise FileNotFoundError(f"No 'Item' (data 3) data was loaded. Check files in '{data_dir}'.")
    
    item_df = pd.concat(all_items, ignore_index=True)
    
    months_of_data = item_df.groupby('Item Name')['Month'].nunique().reset_index().rename(columns={'Month': 'Months_Data'})
    top_items = item_df.groupby('Item Name')[['Amount', 'Count']].sum().reset_index()
    top_items = top_items.sort_values(by='Amount', ascending=False)
    top_items = top_items.merge(months_of_data, on='Item Name', how='left')
    top_items['Avg_Price'] = top_items['Amount'] / top_items['Count']

    # --- 3. Load 'data 2' (Warehouse data) separately ---
    warehouse_files = {
        "May":       {"file": "May_Data_Matrix.xlsx", "sheet": "data 2"},
        "June":      {"file": "June_Data_Matrix.xlsx", "sheet": "data 2"},
        "July":      {"file": "July_Data_Matrix.xlsx", "sheet": "data 2"},
        "August":    {"file": "August_Data_Matrix.xlsx", "sheet": "data 2"},
        "September": {"file": "September_Data_Matrix.xlsx", "sheet": "data 2"},
        "October":   {"file": "October_Data_Matrix_20251103_214000.xlsx", "sheet": "data 2"}
    }
    all_warehouse_data = []
    for month, info in warehouse_files.items():
        full_path = os.path.join(data_dir, info['file'])
        sheet_name = info['sheet']
        if not os.path.exists(full_path):
            print(f"[ERROR] File NOT FOUND: {full_path}")
            continue
        try:
            df = pd.read_excel(full_path, sheet_name=sheet_name)
            df = clean_data(df)
            df['Month'] = month
            all_warehouse_data.append(df)
            print(f"[SUCCESS] Processed: {info['file']} (Sheet: {sheet_name})")
        except Exception as e:
            print(f"[ERROR] Failed to process warehouse file {full_path} (Sheet: {sheet_name}): {e}")
    
    if not all_warehouse_data:
        raise FileNotFoundError(f"No 'Warehouse' (data 2) data was loaded. Check files in '{data_dir}'.")
    
    warehouse_df = pd.concat(all_warehouse_data, ignore_index=True)

    # --- 4. Inventory Analysis Function Call ---
    inventory_table_data, inventory_chart_data, low_stock_alerts = get_inventory_analysis(data_dir, item_df)

    # --- 5. Format for Dashboard ---
    latest_revenue_series = revenue_df[revenue_df['Month'] == 'October']['Total_Revenue']
    latest_revenue = latest_revenue_series.values[0] if not latest_revenue_series.empty else 0
    total_revenue = revenue_df['Total_Revenue'].sum()
    
    best_selling_item_series = item_df.groupby('Item Name')['Count'].sum()
    best_selling_item_name = best_selling_item_series.idxmax()
    best_selling_item_count = best_selling_item_series.max()
    
    try:
        top_warehouse_series = warehouse_df.groupby('Category')['Amount'].sum()
        top_warehouse_name = top_warehouse_series.idxmax()
        top_warehouse_revenue = top_warehouse_series.max()
    except Exception as e:
        print(f"[ERROR] Could not calculate Top Warehouse KPI: {e}")
        top_warehouse_name = "Error"
        top_warehouse_revenue = 0

    highest_rev_item = top_items.iloc[0]
    highest_revenue_item_name = highest_rev_item['Item Name']
    highest_revenue_item_amount = highest_rev_item['Amount']

    worst_selling_item_name = best_selling_item_series.idxmin()
    worst_selling_item_count = best_selling_item_series.min()

    top_5_df = top_items.head(5).copy()
    others_amount = top_items.iloc[5:]['Amount'].sum()
    
    donut_labels = top_5_df['Item Name'].tolist()
    donut_data = top_5_df['Amount'].tolist()
    donut_labels.append("All Others")
    donut_data.append(others_amount)
    
    donut_chart_data = {
        "labels": donut_labels,
        "data": donut_data
    }
    
    top_items_json = top_items.to_json(orient='records')

    # --- 6. Return ALL data (including low_stock_alerts) ---
    return {
        "latest_month_revenue": latest_revenue,
        "total_6_month_revenue": total_revenue,
        "monthly_revenue_df": revenue_df,
        "top_items_json": top_items_json,
        "inventory_table_data": inventory_table_data,
        "inventory_chart_data": inventory_chart_data,
        "best_selling_item_name": best_selling_item_name,
        "best_selling_item_count": best_selling_item_count,
        "top_warehouse_name": top_warehouse_name,
        "top_warehouse_revenue": top_warehouse_revenue,
        "highest_revenue_item_name": highest_revenue_item_name,
        "highest_revenue_item_amount": highest_revenue_item_amount,
        "worst_selling_item_name": worst_selling_item_name,
        "worst_selling_item_count": worst_selling_item_count,
        "donut_chart_data": donut_chart_data,
        "low_stock_alerts": low_stock_alerts  # NEW
    }