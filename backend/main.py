from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from typing import List, Optional
from prophet import Prophet

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
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "your_final_dataset.csv")


def load_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH, parse_dates=["Order Date"])
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
