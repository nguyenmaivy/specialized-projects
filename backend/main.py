from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import os
from typing import List, Optional
from prophet import Prophet
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from datetime import datetime

app = FastAPI(title="AI Sales Forecasting API")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "SampleSuperstore.csv")


def load_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH, encoding='latin-1')
    # Parse date with the format MM/DD/YYYY
    df["Order Date"] = pd.to_datetime(df["Order Date"], format='%m/%d/%Y')
    # Select relevant columns and rename for consistency
    df = df[["Order ID", "Order Date", "Customer ID", "Customer Name", 
             "Region", "Category", "Sales", "Profit", "Discount"]]
    return df


@app.get("/")
def read_root():
    return {"message": "Welcome to AI Sales Forecasting API"}


@app.get("/api/filters")
def get_filters():
    try:
        df = load_data()
        return {
            "categories": df["Category"].unique().tolist(),
            "regions": df["Region"].unique().tolist(),
            "min_date": df["Order Date"].min().date(),
            "max_date": df["Order Date"].max().date()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kpis")
def get_kpis(
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        df = load_data()
        
        # Apply filters
        if category:
            df = df[df["Category"].isin(category)]
        if region:
            df = df[df["Region"].isin(region)]
        if start_date:
            df = df[df["Order Date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["Order Date"] <= pd.to_datetime(end_date)]
            
        return {
            "total_sales": float(df["Sales"].sum()),
            "total_profit": float(df["Profit"].sum()),
            "total_orders": int(df["Order ID"].nunique()),
            "avg_discount": float(df["Discount"].mean())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/sales-trend")
def get_sales_trend(
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        df = load_data()
        
        # Filtering (duplicated logic, should refactor later)
        if category:
            df = df[df["Category"].isin(category)]
        if region:
            df = df[df["Region"].isin(region)]
        if start_date:
            df = df[df["Order Date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["Order Date"] <= pd.to_datetime(end_date)]
            
        sales_over_time = df.groupby("Order Date")["Sales"].sum().reset_index()
        sales_over_time["Order Date"] = sales_over_time["Order Date"].dt.strftime('%Y-%m-%d')
        
        return sales_over_time.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/category-sales")
def get_category_sales(
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        df = load_data()
        
        if category:
            df = df[df["Category"].isin(category)]
        if region:
            df = df[df["Region"].isin(region)]
        if start_date:
            df = df[df["Order Date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["Order Date"] <= pd.to_datetime(end_date)]
        
        cat_sales = df.groupby("Category")["Sales"].sum().sort_values(ascending=False).reset_index()
        return cat_sales.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/region-sales")
def get_region_sales(
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    try:
        df = load_data()
        
        if category:
            df = df[df["Category"].isin(category)]
        if region:
            df = df[df["Region"].isin(region)]
        if start_date:
            df = df[df["Order Date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["Order Date"] <= pd.to_datetime(end_date)]
            
        region_sales = df.groupby("Region")["Sales"].sum().reset_index()
        return region_sales.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast")
def get_forecast(
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None)
):
    try:
        df = load_data()
        
        # Apply filters
        if category:
            df = df[df["Category"].isin(category)]
        if region:
            df = df[df["Region"].isin(region)]
            
        sales_df = df[["Order Date", "Sales"]].rename(columns={"Order Date": "ds", "Sales": "y"})
        sales_df = sales_df.groupby("ds").sum().reset_index()
        
        if len(sales_df) < 50: # Prophet needs some data
             return {"error": "Not enough data for forecasting"}

        m = Prophet()
        m.fit(sales_df)
        future = m.make_future_dataframe(periods=30)
        forecast = m.predict(future)
        
        # Return only the future part or full + future
        # Let's return the last 90 days + 30 days future for visualization
        cols = ["ds", "yhat", "yhat_lower", "yhat_upper"]
        result = forecast[cols].tail(60) # Last 30 historic + 30 future roughly
        result["ds"] = result["ds"].dt.strftime('%Y-%m-%d')
        return result.to_dict(orient="records")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customer-segmentation")
def get_customer_segmentation(
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None)
):
    """
    Perform RFM (Recency, Frequency, Monetary) analysis and K-Means clustering
    to segment customers into: Champions, Loyal, At Risk, and New Customers
    """
    try:
        df = load_data()
        
        # Apply filters
        if category:
            df = df[df["Category"].isin(category)]
        if region:
            df = df[df["Region"].isin(region)]
        
        # Calculate reference date (latest date in dataset)
        reference_date = df["Order Date"].max()
        
        # Calculate RFM metrics per customer
        rfm = df.groupby("Customer ID").agg({
            "Order Date": lambda x: (reference_date - x.max()).days,  # Recency
            "Order ID": "count",  # Frequency
            "Sales": "sum"  # Monetary
        }).reset_index()
        
        rfm.columns = ["Customer ID", "Recency", "Frequency", "Monetary"]
        
        # Add customer names
        customer_names = df[["Customer ID", "Customer Name"]].drop_duplicates()
        rfm = rfm.merge(customer_names, on="Customer ID", how="left")
        
        # Normalize RFM values for clustering
        scaler = StandardScaler()
        rfm_normalized = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])
        
        # K-Means clustering (4 segments)
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        rfm["Cluster"] = kmeans.fit_predict(rfm_normalized)
        
        # Assign meaningful labels based on cluster characteristics
        cluster_stats = rfm.groupby("Cluster").agg({
            "Recency": "mean",
            "Frequency": "mean",
            "Monetary": "mean"
        })
        
        # Label logic: Low Recency + High Frequency + High Monetary = Champions
        # High Recency + Low Frequency = At Risk
        # Medium values = Loyal
        # Low Frequency + Low Monetary = New
        def assign_segment_label(cluster_id):
            stats = cluster_stats.loc[cluster_id]
            recency_rank = cluster_stats["Recency"].rank()[cluster_id]
            frequency_rank = cluster_stats["Frequency"].rank()[cluster_id]
            monetary_rank = cluster_stats["Monetary"].rank()[cluster_id]
            
            if frequency_rank >= 3 and monetary_rank >= 3:
                return "Champions"
            elif recency_rank >= 3:
                return "At Risk"
            elif frequency_rank <= 2 and monetary_rank <= 2:
                return "New Customers"
            else:
                return "Loyal"
        
        rfm["Segment"] = rfm["Cluster"].apply(assign_segment_label)
        
        # Calculate segment statistics
        segment_summary = rfm.groupby("Segment").agg({
            "Customer ID": "count",
            "Recency": "mean",
            "Frequency": "mean",
            "Monetary": "mean"
        }).reset_index()
        
        segment_summary.columns = ["segment", "customer_count", "avg_recency", "avg_frequency", "avg_monetary"]
        
        # Prepare customer-level data for scatter plot
        customers_data = rfm[["Customer ID", "Customer Name", "Recency", "Frequency", "Monetary", "Segment"]].to_dict(orient="records")
        
        return {
            "segments": segment_summary.to_dict(orient="records"),
            "customers": customers_data
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sales-heatmap")
def get_sales_heatmap(
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Return sales data aggregated by date for calendar heatmap visualization
    """
    try:
        df = load_data()
        
        # Apply filters
        if category:
            df = df[df["Category"].isin(category)]
        if region:
            df = df[df["Region"].isin(region)]
        if start_date:
            df = df[df["Order Date"] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df["Order Date"] <= pd.to_datetime(end_date)]
        
        # Aggregate sales by date
        daily_sales = df.groupby("Order Date")["Sales"].sum().reset_index()
        daily_sales["Order Date"] = daily_sales["Order Date"].dt.strftime('%Y-%m-%d')
        daily_sales.columns = ["day", "value"]
        
        return daily_sales.to_dict(orient="records")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

