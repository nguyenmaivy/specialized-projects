from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import numpy as np
import os
import re
import io
import time
from typing import List, Optional
from prophet import Prophet
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from functools import lru_cache
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Load .env file
load_dotenv()

try:
    from backend.auth import (
        UserLogin, UserCreate, Token, UserResponse, ChangePassword,
        authenticate_user, register_user, create_access_token,
        get_current_user, require_admin, users_db,
        change_user_password, delete_user_from_db
    )
except ModuleNotFoundError:
    from auth import (
        UserLogin, UserCreate, Token, UserResponse, ChangePassword,
        authenticate_user, register_user, create_access_token,
        get_current_user, require_admin, users_db,
        change_user_password, delete_user_from_db
    )

# ─── Setup Logging ─────────────────────────────────────────────────────────────

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log rotation: 10MB max, keep 5 backup files
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "app.log"),
    maxBytes=10_000_000,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)

# Date validation pattern
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

# ─── Rate Limiter ──────────────────────────────────────────────────────────────

RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")
limiter = Limiter(key_func=get_remote_address)

# ─── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Sales Forecasting API",
    description="Production-ready AI-powered sales forecasting and customer analytics API",
    version="2.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Setup - configurable via environment variable
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# ─── Request Logging Middleware ────────────────────────────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request: method, path, processing time, status code"""
    start_time = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time}ms "
        f"- IP: {request.client.host if request.client else 'unknown'}"
    )
    return response


# ─── Data Loading ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "SampleSuperstore.csv")


@lru_cache(maxsize=1)
def load_data():
    """Load and cache the data to avoid re-reading CSV on every request"""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")
    df = pd.read_csv(DATA_PATH, encoding='latin-1')
    # Parse date with the format MM/DD/YYYY
    df["Order Date"] = pd.to_datetime(df["Order Date"], format='%m/%d/%Y')
    # Select relevant columns and rename for consistency
    df = df[["Order ID", "Order Date", "Customer ID", "Customer Name", 
             "Region", "Category", "Sales", "Profit", "Discount"]]
    logger.info(f"✅ Data loaded successfully: {len(df)} records")
    return df


# ─── Helper Functions ──────────────────────────────────────────────────────────

def validate_date(date_str: str) -> bool:
    """Validate date string format (YYYY-MM-DD)"""
    if not DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def apply_filters(
    df: pd.DataFrame,
    category: Optional[List[str]] = None,
    region: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Helper function to apply filters consistently across all endpoints.
    
    Args:
        df: Input dataframe
        category: List of categories to filter
        region: List of regions to filter
        start_date: Start date as string (YYYY-MM-DD)
        end_date: End date as string (YYYY-MM-DD)
    
    Returns:
        Filtered dataframe
    
    Raises:
        ValueError: If date format is invalid
    """
    if category:
        df = df[df["Category"].isin(category)]
    if region:
        df = df[df["Region"].isin(region)]
    if start_date:
        if not validate_date(start_date):
            raise ValueError(f"Invalid start_date format: '{start_date}'. Expected YYYY-MM-DD")
        df = df[df["Order Date"] >= pd.to_datetime(start_date)]
    if end_date:
        if not validate_date(end_date):
            raise ValueError(f"Invalid end_date format: '{end_date}'. Expected YYYY-MM-DD")
        df = df[df["Order Date"] <= pd.to_datetime(end_date)]
    
    return df


# =============================================================================
# AUTH ENDPOINTS
# =============================================================================

@app.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, user_data: UserLogin):
    """Authenticate user and return JWT token"""
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        logger.warning(f"❌ Failed login attempt for user: {user_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    logger.info(f"✅ User logged in: {user['username']}")
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=int(os.getenv("TOKEN_EXPIRE_MINUTES", "60")) * 60
    )


@app.post("/auth/register", response_model=UserResponse)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserCreate, admin: dict = Depends(require_admin)):
    """Register a new user with specific role (admin only)"""
    try:
        result = register_user(user_data.username, user_data.password, user_data.role)
        return UserResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/signup", response_model=UserResponse)
@limiter.limit("5/minute")
def signup(request: Request, user_data: UserCreate):
    """Public signup endpoint (forces 'viewer' role)"""
    try:
        # Force role to viewer for public signups regardless of input
        result = register_user(user_data.username, user_data.password, "viewer")
        return UserResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info"""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UserResponse(username=current_user["username"], role=current_user["role"])


@app.get("/auth/users")
def list_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)"""
    return [
        {"username": u["username"], "role": u["role"]}
        for u in users_db.values()
    ]


@app.put("/auth/change-password")
def change_password(request: Request, data: ChangePassword, current_user: dict = Depends(get_current_user)):
    """Change password for current authenticated user"""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        result = change_user_password(current_user["username"], data.current_password, data.new_password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/auth/users/{username}")
def delete_user(username: str, admin: dict = Depends(require_admin)):
    """Delete a user (admin only)"""
    try:
        result = delete_user_from_db(username)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """Logout current user (client should discard the token)"""
    username = current_user["username"] if current_user else "anonymous"
    logger.info(f"✅ User logged out: {username}")
    return {"message": "Logged out successfully", "detail": "Please discard your token on client side"}


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@app.get("/")
def read_root():
    return {"message": "Welcome to AI Sales Forecasting API"}


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers"""
    try:
        df = load_data()
        return {
            "status": "healthy",
            "version": "2.0.0",
            "records_loaded": len(df),
            "auth_required": os.getenv("AUTH_REQUIRED", "false"),
            "rate_limit": RATE_LIMIT,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# =============================================================================
# API ENDPOINTS (Protected when AUTH_REQUIRED=true)
# =============================================================================

@app.get("/api/filters")
@limiter.limit(RATE_LIMIT)
def get_filters(request: Request, current_user: dict = Depends(get_current_user)):
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
@limiter.limit(RATE_LIMIT)
def get_kpis(
    request: Request,
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        df = load_data()
        df = apply_filters(df, category, region, start_date, end_date)
        
        # Handle empty DataFrame after filtering
        if df.empty:
            return {
                "total_sales": 0,
                "total_profit": 0,
                "total_orders": 0,
                "avg_discount": 0
            }
            
        return {
            "total_sales": float(df["Sales"].sum()),
            "total_profit": float(df["Profit"].sum()),
            "total_orders": int(df["Order ID"].nunique()),
            "avg_discount": float(df["Discount"].mean())
        }
    except ValueError as e:
        logger.warning(f"Validation error in get_kpis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_kpis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/sales-trend")
@limiter.limit(RATE_LIMIT)
def get_sales_trend(
    request: Request,
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        df = load_data()
        df = apply_filters(df, category, region, start_date, end_date)
            
        sales_over_time = df.groupby("Order Date")["Sales"].sum().reset_index()
        sales_over_time["Order Date"] = sales_over_time["Order Date"].dt.strftime('%Y-%m-%d')
        
        return sales_over_time.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error in get_sales_trend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/category-sales")
@limiter.limit(RATE_LIMIT)
def get_category_sales(
    request: Request,
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        df = load_data()
        df = apply_filters(df, category, region, start_date, end_date)
        
        cat_sales = df.groupby("Category")["Sales"].sum().sort_values(ascending=False).reset_index()
        return cat_sales.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error in get_category_sales: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/charts/region-sales")
@limiter.limit(RATE_LIMIT)
def get_region_sales(
    request: Request,
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    try:
        df = load_data()
        df = apply_filters(df, category, region, start_date, end_date)
            
        region_sales = df.groupby("Region")["Sales"].sum().reset_index()
        return region_sales.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error in get_region_sales: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast")
@limiter.limit(RATE_LIMIT)
def get_forecast(
    request: Request,
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        df = load_data()
        df = apply_filters(df, category, region, None, None)
            
        sales_df = df[["Order Date", "Sales"]].rename(columns={"Order Date": "ds", "Sales": "y"})
        sales_df = sales_df.groupby("ds").sum().reset_index()
        
        if len(sales_df) < 50: # Prophet needs some data
             logger.warning("Insufficient data for forecasting")
             return {"error": "Not enough data for forecasting"}

        m = Prophet(interval_width=0.95)
        m.fit(sales_df)
        future = m.make_future_dataframe(periods=30)
        forecast = m.predict(future)
        
        cols = ["ds", "yhat", "yhat_lower", "yhat_upper"]
        result = forecast[cols].tail(60)
        result["ds"] = result["ds"].dt.strftime('%Y-%m-%d')
        logger.info("✅ Forecast generated successfully")
        return result.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error in get_forecast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/customer-segmentation")
@limiter.limit(RATE_LIMIT)
def get_customer_segmentation(
    request: Request,
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Perform RFM (Recency, Frequency, Monetary) analysis and K-Means clustering
    to segment customers into: Champions, Loyal, At Risk, and New Customers
    """
    try:
        df = load_data()
        df = apply_filters(df, category, region, None, None)
        
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
        
        def assign_segment_label(cluster_id):
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
        
        customers_data = rfm[["Customer ID", "Customer Name", "Recency", "Frequency", "Monetary", "Segment"]].to_dict(orient="records")
        
        logger.info("✅ Customer segmentation completed")
        return {
            "segments": segment_summary.to_dict(orient="records"),
            "customers": customers_data
        }
    except Exception as e:
        logger.error(f"Error in get_customer_segmentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/sales-heatmap")
@limiter.limit(RATE_LIMIT)
def get_sales_heatmap(
    request: Request,
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Return sales data aggregated by date for calendar heatmap visualization"""
    try:
        df = load_data()
        df = apply_filters(df, category, region, start_date, end_date)
        
        # Aggregate sales by date
        daily_sales = df.groupby("Order Date")["Sales"].sum().reset_index()
        daily_sales["Order Date"] = daily_sales["Order Date"].dt.strftime('%Y-%m-%d')
        daily_sales.columns = ["day", "value"]
        
        logger.info(f"✅ Heatmap data generated: {len(daily_sales)} days")
        return daily_sales.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error in get_sales_heatmap: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXPORT ENDPOINT
# =============================================================================

@app.get("/api/export/csv")
@limiter.limit("10/minute")
def export_csv(
    request: Request,
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Export filtered sales data as CSV file download"""
    try:
        df = load_data()
        df = apply_filters(df, category, region, start_date, end_date)
        
        # Convert to CSV
        output = io.StringIO()
        export_df = df.copy()
        export_df["Order Date"] = export_df["Order Date"].dt.strftime('%Y-%m-%d')
        export_df.to_csv(output, index=False)
        output.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sales_export_{timestamp}.csv"
        
        logger.info(f"✅ CSV export: {len(df)} records")
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in export_csv: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
