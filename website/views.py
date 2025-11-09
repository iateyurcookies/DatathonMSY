from flask import Blueprint, render_template, json
from .analysis import get_dashboard_data  # Import our function
import numpy as np # Import numpy for calculations
from datetime import datetime

views = Blueprint("views", __name__)

def get_next_month(last_month_str):
    """Helper to get the next month's 3-letter abbreviation"""
    try:
        # Get the month number (1-12)
        last_month_num = datetime.strptime(last_month_str, '%B').month
        # Get the next month's number
        next_month_num = 1 if last_month_num == 12 else last_month_num + 1
        # Get the 3-letter name for the next month
        return datetime(2025, next_month_num, 1).strftime('%b')
    except:
        return "Nov" # Fallback

@views.route("/")
def home():
    # 1. Get all the data from our analysis file
    dashboard_data = get_dashboard_data()
    
    # 2. Prepare data for the chart
    monthly_df = dashboard_data['monthly_revenue_df']
    chart_labels = monthly_df['Month'].tolist()
    chart_values = monthly_df['Total_Revenue'].tolist()

    # --- 3. Calculate Prediction Range ---
    x = np.array(range(len(chart_values)))
    y = np.array(chart_values)
    
    # Fit a 1st-degree (linear) model
    model = np.polyfit(x, y, 1)
    predict = np.poly1d(model)
    
    # Calculate residuals (errors)
    residuals = y - predict(x)
    std_error = np.std(residuals)
    
    # Predict the next month (index 6)
    predicted_revenue = predict(len(x))
    good_month_pred = predicted_revenue + std_error
    bad_month_pred = predicted_revenue - std_error
    
    # Create dataset for the main prediction line
    prediction_data = [None] * len(chart_values)
    prediction_data[-1] = chart_values[-1] # Connects the line
    prediction_data.append(predicted_revenue)
    
    # Create dataset for the "Good Month" line
    good_month_data = [None] * len(chart_values)
    good_month_data[-1] = chart_values[-1]
    good_month_data.append(good_month_pred)

    # Create dataset for the "Bad Month" line
    bad_month_data = [None] * len(chart_values)
    bad_month_data[-1] = chart_values[-1]
    bad_month_data.append(bad_month_pred)
    
    # Add the next month to the labels
    next_month = get_next_month(chart_labels[-1])
    chart_labels.append(next_month)
    # --- End of Prediction ---

    # 4. Pass all the data to the template
    return render_template(
        "home.html",
        # KPI Cards
        latest_revenue=f"${dashboard_data['latest_month_revenue']:,.2f}",
        annual_revenue=f"${dashboard_data['total_6_month_revenue']:,.2f}",
        
        best_item_name=dashboard_data['best_selling_item_name'],
        best_item_count=f"{dashboard_data['best_selling_item_count']:,} units",
        top_warehouse_name=dashboard_data['top_warehouse_name'],
        top_warehouse_revenue=f"${dashboard_data['top_warehouse_revenue']:,.2f} in revenue",
        
        # --- NEW KPI VARIABLES ---
        highest_rev_item_name=dashboard_data['highest_revenue_item_name'],
        highest_rev_item_amount=f"${dashboard_data['highest_revenue_item_amount']:,.2f}",
        worst_item_name=dashboard_data['worst_selling_item_name'],
        worst_item_count=f"{dashboard_data['worst_selling_item_count']:,} units",
        # --- End of new KPIs ---
        
        # Chart Data
        chart_labels=json.dumps(chart_labels),
        chart_data=json.dumps(chart_values),
        prediction_data=json.dumps(prediction_data),
        good_month_data=json.dumps(good_month_data),
        bad_month_data=json.dumps(bad_month_data),
        
        # Donut Chart Data
        donut_chart_data=json.dumps(dashboard_data['donut_chart_data']),
        
        # --- NEW: Low Stock Alerts ---
        low_stock_alerts=dashboard_data['low_stock_alerts']
    )

@views.route("/charts")
def charts():
    # 1. Get all the data from our analysis file
    dashboard_data = get_dashboard_data()
    
    # 2. Prepare data for the monthly chart
    monthly_df = dashboard_data['monthly_revenue_df']
    chart_labels = monthly_df['Month'].tolist()
    chart_values = monthly_df['Total_Revenue'].tolist()

    # --- 3. Calculate Prediction Range ---
    x = np.array(range(len(chart_values)))
    y = np.array(chart_values)
    model = np.polyfit(x, y, 1)
    predict = np.poly1d(model)
    
    residuals = y - predict(x)
    std_error = np.std(residuals)
    
    predicted_revenue = predict(len(x))
    good_month_pred = predicted_revenue + std_error
    bad_month_pred = predicted_revenue - std_error
    
    prediction_data = [None] * len(chart_values)
    prediction_data[-1] = chart_values[-1]
    prediction_data.append(predicted_revenue)
    
    good_month_data = [None] * len(chart_values)
    good_month_data[-1] = chart_values[-1]
    good_month_data.append(good_month_pred)

    bad_month_data = [None] * len(chart_values)
    bad_month_data[-1] = chart_values[-1]
    bad_month_data.append(bad_month_pred)
    
    next_month = get_next_month(chart_labels[-1])
    chart_labels.append(next_month)
    # --- End of Prediction ---

    # 4. Pass ALL chart data to charts.html
    return render_template(
        "charts.html",
        # Monthly Revenue Chart
        chart_labels=json.dumps(chart_labels),
        chart_data=json.dumps(chart_values),
        prediction_data=json.dumps(prediction_data),
        good_month_data=json.dumps(good_month_data),
        bad_month_data=json.dumps(bad_month_data),
        
        # Inventory Chart
        inventory_chart_data=json.dumps(dashboard_data['inventory_chart_data']),
        
        # Donut Chart
        donut_chart_data=json.dumps(dashboard_data['donut_chart_data']),
        
        # --- NEW: Low Stock Alerts ---
        low_stock_alerts=dashboard_data['low_stock_alerts']
    )

@views.route("/tables")
def tables():
    # 1. Get all the data from our analysis file
    dashboard_data = get_dashboard_data()

    # 3. Pass BOTH tables to tables.html
    return render_template(
        "tables.html",
        top_items_data=dashboard_data['top_items_json'],
        inventory_data=dashboard_data['inventory_table_data'],
        
        # --- NEW: Low Stock Alerts ---
        low_stock_alerts=dashboard_data['low_stock_alerts']
    )