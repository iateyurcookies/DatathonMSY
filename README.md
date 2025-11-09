# Mai Shan Yun Inventory Intelligence Dashboard

## Overview

The Mai Shan Yun Inventory Intelligence Dashboard is an interactive web application designed to transform raw restaurant data into actionable insights for inventory management. Built with Flask and powered by data analytics, this dashboard helps restaurant managers optimize inventory levels, minimize waste, avoid shortages, and predict restocking needs.

## Purpose & Key Insights

This dashboard empowers restaurant managers to:

- **Monitor Inventory Levels**: Track which ingredients are running low, overstocked, or optimally stocked
- **Analyze Sales Trends**: Visualize monthly revenue patterns and predict future performance
- **Optimize Ingredient Usage**: Understand how menu item sales affect ingredient consumption over time
- **Prevent Stockouts**: Receive automated low-stock alerts before ingredients run out
- **Reduce Waste**: Identify surplus ingredients to minimize spoilage and waste
- **Make Data-Driven Decisions**: Access predictive analytics for ingredient reordering

## Key Features

### Interactive Visualizations

- **Monthly Revenue Trends**: Line chart with predictive forecasting for next month's revenue (best/worst case scenarios)
- **Inventory Status Chart**: Color-coded bar chart showing stock levels (Low Stock, Stocked, Surplus)
- **Revenue Distribution**: Donut chart displaying top-selling items and their contribution to total revenue

### Ingredient Insights

- **Inventory Analysis**: Real-time tracking of 14+ key ingredients with usage vs. shipment comparison
- **Smart Status Indicators**: Automatic classification of ingredients as Low Stock, Stocked, or Surplus
- **Usage Calculations**: Average monthly usage based on recipe requirements and actual sales data

### Predictive Analytics

- **Revenue Forecasting**: Linear regression model predicting next month's revenue with confidence intervals
- **Reorder Alerts**: Automated notifications when ingredient buffers fall below 1 week of usage
- **Trend Analysis**: 6-month historical data analysis to identify seasonal patterns

### Real-Time Alerts

- **Low Stock Notifications**: Dashboard alerts highlighting ingredients requiring immediate attention
- **Buffer Analysis**: Clear indicators showing weeks of inventory remaining for each ingredient

## Datasets Used & Integration

The dashboard integrates multiple data sources from Mai Shan Yun restaurant:

1. **Monthly Sales Data** (May - October 2024)

   - Files: `May_Data_Matrix.xlsx` through `October_Data_Matrix.xlsx`
   - Sheets: `data 1` (revenue), `data 2` (warehouse), `data 3` (item sales)
   - Provides: Monthly revenue, item-level sales counts, warehouse performance

2. **Ingredient Recipe Data**

   - File: `MSY Data - Ingredient.csv`
   - Provides: Recipe requirements for each menu item (quantities in grams, pieces, counts)
   - Includes: 14 menu items with detailed ingredient breakdowns

3. **Shipment Data**
   - File: `MSY Data - Shipment.csv`
   - Provides: Supplier shipment schedules, quantities, and frequencies
   - Includes: 14 key ingredients with weekly/biweekly/monthly delivery schedules

### Data Integration Process

1. **Sales Aggregation**: Combines 6 months of sales data across all menu items
2. **Recipe Mapping**: Links menu item sales to ingredient consumption using recipe data
3. **Shipment Normalization**: Converts various shipment units (lbs, pieces, rolls) to standardized units (grams)
4. **Inventory Calculation**: Compares monthly ingredient usage against shipment volumes
5. **Status Classification**: Assigns Low Stock/Stocked/Surplus status based on buffer thresholds

## Technical Architecture

- **Backend**: Flask (Python web framework)
- **Data Processing**: Pandas, NumPy
- **Database**: SQLAlchemy with SQLite
- **Frontend**: Bootstrap 5, Chart.js
- **Predictive Modeling**: NumPy polynomial regression

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd DatathonMSY
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare data files**

   - Ensure all data files are placed in the `website/data/` directory:
     - `May_Data_Matrix.xlsx`
     - `June_Data_Matrix.xlsx`
     - `July_Data_Matrix.xlsx`
     - `August_Data_Matrix.xlsx`
     - `September_Data_Matrix.xlsx`
     - `October_Data_Matrix_20251103_214000.xlsx`
     - `MSY Data - Ingredient.csv`
     - `MSY Data - Shipment.csv`

4. **Run the application**

   ```bash
   python main.py
   ```

5. **Access the dashboard**
   - Open your web browser and navigate to: `http://127.0.0.1:5000`

## Usage Guide

### Dashboard Pages

1. **Home** (`/`)

   - Overview KPIs: Latest month revenue, 6-month total, best/worst sellers
   - Monthly revenue chart with predictive forecasting
   - Low stock alerts panel
   - Revenue distribution donut chart

2. **Charts** (`/charts`)

   - Detailed inventory status visualization
   - Interactive bar chart showing stock deltas for all ingredients
   - Color-coded status indicators (red = low stock, green = stocked, yellow = surplus)

3. **Tables** (`/tables`)
   - Comprehensive inventory table with detailed metrics
   - Top-selling items ranked by revenue
   - Sortable columns for easy analysis

## Example Insights & Use Cases

### Use Case 1: Preventing Stockouts

**Scenario**: The dashboard shows "Chicken" with a Low Stock status and buffer < 1 week.  
**Action**: Manager immediately contacts supplier to schedule an emergency shipment.  
**Impact**: Prevents menu item unavailability and customer dissatisfaction.

### Use Case 2: Reducing Waste

**Scenario**: "White Onion" shows Surplus status with 8 weeks of buffer.  
**Action**: Manager reduces next month's order quantity by 50%.  
**Impact**: Reduces spoilage costs and frees up storage space.

### Use Case 3: Revenue Forecasting

**Scenario**: Dashboard predicts November revenue between $45K-$55K (vs. October's $50K).  
**Action**: Manager adjusts staffing levels and ingredient orders accordingly.  
**Impact**: Optimizes labor costs and prevents over/under-ordering.

### Use Case 4: Menu Optimization

**Scenario**: Tables page shows "Beef Noodle Soup" generates $12K revenue but "Vegetable Fried Rice" only $800.  
**Action**: Manager considers promoting high-revenue items or discontinuing low performers.  
**Impact**: Maximizes profitability and simplifies inventory management.

## Predictive Features

### Revenue Forecasting Model

- **Algorithm**: Linear regression with standard error calculation
- **Inputs**: 6 months of historical revenue data
- **Outputs**:
  - Base prediction for next month
  - Optimistic scenario (prediction + 1 std error)
  - Pessimistic scenario (prediction - 1 std error)
- **Visualization**: Three-line chart showing historical data and future projections

### Inventory Prediction Logic

- **Safety Stock Threshold**: 25% of monthly usage (≈1 week buffer)
- **Surplus Threshold**: 150% of monthly usage (≈6 weeks buffer)
- **Status Assignment**:
  - Low Stock: Buffer < 1 week → Immediate reorder needed
  - Stocked: Buffer between 1-6 weeks → Optimal range
  - Surplus: Buffer > 6 weeks → Reduce next order

## Project Structure

```
DatathonMSY/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── website/
    ├── __init__.py              # Flask app initialization
    ├── views.py                 # Route handlers and view logic
    ├── auth.py                  # Authentication routes
    ├── models.py                # Database models
    ├── analysis.py              # Core data analysis engine
    ├── data/                    # Data files directory
    │   ├── *.xlsx               # Monthly sales data
    │   ├── MSY Data - Ingredient.csv
    │   └── MSY Data - Shipment.csv
    ├── templates/               # HTML templates
    │   ├── home.html
    │   ├── charts.html
    │   └── tables.html
    └── static/                  # CSS, JS, images
        ├── css/
        ├── js/
        └── images/
```

## Technologies Used

- **Python 3.8+**: Core programming language
- **Flask**: Web framework for routing and templating
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing and predictive modeling
- **SQLAlchemy**: Database ORM
- **Bootstrap 5**: Responsive UI framework
- **Chart.js**: Interactive data visualizations
- **Flask-Bootstrap**: Bootstrap integration for Flask

## Future Enhancements

- Real-time data integration with POS systems
- Machine learning models for demand forecasting
- Multi-location support for restaurant chains
- Mobile-responsive design improvements
- Export functionality for reports (PDF, Excel)
- Integration with supplier ordering systems
- Historical trend comparison (year-over-year)

## Contributors

Developed for the Mai Shan Yun Inventory Intelligence Challenge

## License

This project is created for educational and competition purposes.
