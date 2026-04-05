from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import numpy as np
import os
import re
import io
import time
import json
import uuid
import requests
from pydantic import BaseModel

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None
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

try:
    from backend.db import (
        is_db_enabled,
        init_db,
        seed_default_dataset_from_csv,
        load_active_orders,
        get_active_dataset_id,
        save_analysis_run,
        get_analysis_run,
        save_widgets,
        create_dataset,
        set_active_dataset,
        insert_orders,
        create_ingestion_run,
        update_ingestion_run,
        save_column_mapping,
        save_knowledge_chunks,
        search_knowledge,
        get_all_knowledge_for_dataset,
        save_chat_history,
        get_recent_chat_history,
        get_raw_data_sample,
        get_data_statistics,
    )
except ModuleNotFoundError:
    from db import (
        is_db_enabled,
        init_db,
        seed_default_dataset_from_csv,
        load_active_orders,
        get_active_dataset_id,
        save_analysis_run,
        get_analysis_run,
        save_widgets,
        create_dataset,
        set_active_dataset,
        insert_orders,
        create_ingestion_run,
        update_ingestion_run,
        save_column_mapping,
        save_knowledge_chunks,
        search_knowledge,
        get_all_knowledge_for_dataset,
        save_chat_history,
        get_recent_chat_history,
        get_raw_data_sample,
        get_data_statistics,
    )

# ─── Setup Logging ─────────────────────────────────────────────────────────────

# Put logs outside the watched backend/ directory to avoid triggering the reloader
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs"))
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

class FiltersPayload(BaseModel):
    category: Optional[List[str]] = None
    region: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AnalysisInsightRequest(BaseModel):
    analysis_run_id: str


class ChatRequest(BaseModel):
    analysis_run_id: str
    message: str


def _get_openai_client():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.io/api/v1").rstrip("/")

    if OpenAI is not None:
        try:
            return OpenAI(api_key=api_key, base_url=base_url)
        except Exception:
            pass

    class _SimpleCompletions:
        def __init__(self, api_key, base_url):
            self.api_key = api_key
            self.base_url = base_url

        def create(self, model, temperature=0.7, response_format=None, messages=None, max_tokens=512, **kwargs):
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": model,
                "messages": messages or [],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            class _Msg:
                def __init__(self, content):
                    self.message = type("_", (), {"content": content})

            choices = []
            if isinstance(data, dict) and "choices" in data and len(data["choices"]) > 0:
                first = data["choices"][0]
                content = None
                if isinstance(first, dict):
                    content = first.get("message", {}).get("content") if first.get("message") else first.get("text")
                else:
                    content = str(first)
                choices = [_Msg(content)]
            else:
                choices = [_Msg(json.dumps(data, ensure_ascii=False))]

            return type("_", (), {"choices": choices})

    class _SimpleChat:
        def __init__(self, api_key, base_url):
            self.completions = _SimpleCompletions(api_key, base_url)

    class _SimpleClient:
        def __init__(self, api_key, base_url):
            self.chat = _SimpleChat(api_key, base_url)

    return _SimpleClient(api_key, base_url)


def _coerce_for_json(value):
    if isinstance(value, (np.generic,)):
        return value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, dict):
        return {k: _coerce_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_for_json(v) for v in value]
    return value


def _compute_analysis_bundle(filters: FiltersPayload):
    try:
        df = load_data()
        logger.info(f"load_data thành công: {len(df)} records, columns: {df.columns.tolist()}")
    except Exception as e:
        logger.error(f"load_data thất bại: {e}")
        df = pd.DataFrame()

    try:
        filtered = apply_filters(
            df,
            filters.category,
            filters.region,
            filters.start_date,
            filters.end_date,
        )
    except Exception as e:
        logger.warning(f"apply_filters lỗi: {e}")
        filtered = pd.DataFrame()

    if filtered.empty:
        logger.warning("Dữ liệu sau filter rỗng → trả về bundle mặc định")
        return {
            "kpis": {"total_sales": 0, "total_profit": 0, "total_orders": 0, "avg_discount": 0},
            "sales_trend": [],
            "category_sales": [],
            "region_sales": [],
            "forecast": [],
            "rfm": {"segments": [], "customers": []},
            "what_if": {
                "discount_scenario": {"delta_discount_pct": 1.0, "uplift_sales": 0, "uplift_profit": 0},
                "at_risk_scenario": {"conversion_rate": 0.1, "uplift_sales": 0, "uplift_profit": 0},
            },
        }

    try:
        kpis = {
            "total_sales": float(filtered["Sales"].sum()),
            "total_profit": float(filtered["Profit"].sum()),
            "total_orders": int(filtered["Order ID"].nunique()),
            "avg_discount": float(filtered["Discount"].mean()),
        }
    except Exception as e:
        logger.warning(f"Tính KPI lỗi: {e}")
        kpis = {"total_sales": 0, "total_profit": 0, "total_orders": 0, "avg_discount": 0}

    try:
        sales_trend = filtered.groupby("Order Date")["Sales"].sum().reset_index()
        sales_trend["Order Date"] = sales_trend["Order Date"].dt.strftime('%Y-%m-%d')
        sales_trend = sales_trend.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"Sales trend lỗi: {e}")
        sales_trend = []

    try:
        category_sales = filtered.groupby("Category")["Sales"].sum().sort_values(ascending=False).reset_index().to_dict(orient="records")
        region_sales = filtered.groupby("Region")["Sales"].sum().reset_index().to_dict(orient="records")
    except Exception as e:
        logger.warning(f"Category/Region sales lỗi: {e}")
        category_sales = []
        region_sales = []

    forecast_data = []
    try:
        sales_df = filtered[["Order Date", "Sales"]].rename(columns={"Order Date": "ds", "Sales": "y"}).groupby("ds").sum().reset_index()
        if len(sales_df) >= 50:
            model = Prophet(interval_width=0.95)
            model.fit(sales_df)
            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)
            forecast_data = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(60)
            forecast_data["ds"] = forecast_data["ds"].dt.strftime('%Y-%m-%d')
            forecast_data = forecast_data.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"Forecast lỗi: {e}")

    try:
        reference_date = filtered["Order Date"].max()
        rfm = filtered.groupby("Customer ID").agg({
            "Order Date": lambda x: (reference_date - x.max()).days,
            "Order ID": "count",
            "Sales": "sum",
        }).reset_index()
        rfm.columns = ["Customer ID", "Recency", "Frequency", "Monetary"]

        customer_names = filtered[["Customer ID", "Customer Name"]].drop_duplicates()
        rfm = rfm.merge(customer_names, on="Customer ID", how="left")

        if len(rfm) >= 4:
            scaler = StandardScaler()
            rfm_scaled = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])
            kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
            rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)

            cluster_stats = rfm.groupby("Cluster").agg({"Recency": "mean", "Frequency": "mean", "Monetary": "mean"})

            def _segment_label(cluster_id):
                recency_rank = cluster_stats["Recency"].rank()[cluster_id]
                frequency_rank = cluster_stats["Frequency"].rank()[cluster_id]
                monetary_rank = cluster_stats["Monetary"].rank()[cluster_id]
                if frequency_rank >= 3 and monetary_rank >= 3:
                    return "Champions"
                if recency_rank >= 3:
                    return "At Risk"
                if frequency_rank <= 2 and monetary_rank <= 2:
                    return "New Customers"
                return "Loyal"

            rfm["Segment"] = rfm["Cluster"].apply(_segment_label)
        else:
            rfm["Segment"] = "Unclassified"

        segment_summary = rfm.groupby("Segment").agg({
            "Customer ID": "count",
            "Recency": "mean",
            "Frequency": "mean",
            "Monetary": "mean",
        }).reset_index()
        segment_summary.columns = ["segment", "customer_count", "avg_recency", "avg_frequency", "avg_monetary"]

        rfm_result = {
            "segments": segment_summary.to_dict(orient="records"),
            "customers": rfm[["Customer ID", "Customer Name", "Recency", "Frequency", "Monetary", "Segment"]].to_dict(orient="records"),
        }
    except Exception as e:
        logger.warning(f"RFM segmentation lỗi: {e}")
        rfm_result = {"segments": [], "customers": []}

    try:
        margin = (kpis["total_profit"] / kpis["total_sales"]) if kpis["total_sales"] > 0 else 0
        discount_sensitivity = float(np.nan_to_num(filtered[["Discount", "Sales"]].corr().iloc[0, 1], nan=0.0))
        delta_discount_pct = 1.0
        uplift_sales = kpis["total_sales"] * (discount_sensitivity * (delta_discount_pct / 100))
        uplift_profit = uplift_sales * margin

        at_risk_segment = next((s for s in rfm_result["segments"] if s["segment"] == "At Risk"), None)
        total_customers = max(sum(int(s["customer_count"]) for s in rfm_result["segments"]), 1)
        at_risk_share = (at_risk_segment["customer_count"] / total_customers) if at_risk_segment else 0
        conversion_rate = 0.1
        avg_monetary_at_risk = at_risk_segment["avg_monetary"] if at_risk_segment else 0
        uplift_sales_at_risk = float(avg_monetary_at_risk) * conversion_rate * float(at_risk_share)

        what_if = {
            "discount_scenario": {
                "delta_discount_pct": delta_discount_pct,
                "discount_sensitivity": discount_sensitivity,
                "margin_assumption": margin,
                "uplift_sales": float(uplift_sales),
                "uplift_profit": float(uplift_profit),
            },
            "at_risk_scenario": {
                "conversion_rate": conversion_rate,
                "at_risk_share": float(at_risk_share),
                "avg_monetary_at_risk": float(avg_monetary_at_risk),
                "uplift_sales": float(uplift_sales_at_risk),
                "uplift_profit": float(uplift_sales_at_risk * margin),
            },
        }
    except Exception as e:
        logger.warning(f"What-if calculation lỗi: {e}")
        what_if = {"discount_scenario": {}, "at_risk_scenario": {}}

    return {
        "kpis": kpis,
        "sales_trend": sales_trend,
        "category_sales": category_sales,
        "region_sales": region_sales,
        "forecast": forecast_data,
        "rfm": rfm_result,
        "what_if": what_if,
    }


# def _default_widgets(evidence: dict):
#     # Build richer Vietnamese insights using available evidence
#     kpis = evidence.get("kpis", {})
#     what_if = evidence.get("what_if", {})
#     forecast = evidence.get("forecast", [])
#     sales_trend = evidence.get("sales_trend", [])

#     total_sales = float(kpis.get("total_sales", 0) or 0)
#     total_profit = float(kpis.get("total_profit", 0) or 0)
#     total_orders = int(kpis.get("total_orders", 0) or 0)

#     # Prepare sales trend DataFrame if available
#     try:
#         df_trend = pd.DataFrame(sales_trend)
#         if not df_trend.empty and "Order Date" in df_trend.columns:
#             df_trend["Order Date"] = pd.to_datetime(df_trend["Order Date"])
#             df_trend = df_trend.sort_values("Order Date")
#             df_trend["year"] = df_trend["Order Date"].dt.year
#             df_trend["month"] = df_trend["Order Date"].dt.month
#             df_trend["month_label"] = df_trend["Order Date"].dt.strftime("%m/%Y")
#         else:
#             df_trend = pd.DataFrame()
#     except Exception:
#         df_trend = pd.DataFrame()

#     # Compute notable points
#     max_month = None
#     min_month = None
#     recent_growth_pct = None
#     mom_max = None
#     mom_min = None
#     trend_text = "không rõ"

#     try:
#         if not df_trend.empty:
#             # aggregate by month
#             df_month = df_trend.copy()
#             df_month = df_month.groupby([df_month["Order Date"].dt.to_period("M")])["Sales"].sum().reset_index()
#             df_month["Order Date"] = df_month["Order Date"].dt.to_timestamp()
#             df_month = df_month.sort_values("Order Date")

#             max_row = df_month.loc[df_month["Sales"].idxmax()]
#             min_row = df_month.loc[df_month["Sales"].idxmin()]
#             max_month = (max_row["Order Date"].strftime("%b %Y"), float(max_row["Sales"]))
#             min_month = (min_row["Order Date"].strftime("%b %Y"), float(min_row["Sales"]))

#             # Recent growth: compare last month vs first month in the series
#             first = df_month.iloc[0]["Sales"]
#             last = df_month.iloc[-1]["Sales"]
#             if first and not np.isclose(first, 0):
#                 recent_growth_pct = (last - first) / first * 100
#             else:
#                 recent_growth_pct = None

#             # month-over-month changes
#             df_month["pct_change"] = df_month["Sales"].pct_change() * 100
#             if df_month["pct_change"].dropna().size:
#                 mom_max_row = df_month.loc[df_month["pct_change"].idxmax()]
#                 mom_min_row = df_month.loc[df_month["pct_change"].idxmin()]
#                 mom_max = (mom_max_row["Order Date"].strftime("%b %Y"), float(mom_max_row["pct_change"]))
#                 mom_min = (mom_min_row["Order Date"].strftime("%b %Y"), float(mom_min_row["pct_change"]))

#             # Trend: simple linear fit on months
#             try:
#                 xs = np.arange(len(df_month))
#                 ys = df_month["Sales"].values.astype(float)
#                 if len(xs) > 1 and not np.allclose(ys, ys[0]):
#                     slope = np.polyfit(xs, ys, 1)[0]
#                     trend_text = "tăng" if slope > 0 else "giảm" if slope < 0 else "ổn định"
#             except Exception:
#                 pass
#     except Exception:
#         pass

#     # Forecast summary (next 3 points if available)
#     forecast_summary = []
#     try:
#         if forecast and isinstance(forecast, list):
#             last_three = forecast[-3:]
#             for f in last_three:
#                 ds = f.get("ds")
#                 yhat = float(f.get("yhat", 0) or 0)
#                 forecast_summary.append((ds, yhat))
#     except Exception:
#         forecast_summary = []

#     # Compose Vietnamese markdown matching the example: bold summary + bullet insights
#     period_start = None
#     period_end = None
#     try:
#         if not df_trend.empty:
#             period_start = df_trend["Order Date"].iloc[0].strftime('%b %Y')
#             period_end = df_trend["Order Date"].iloc[-1].strftime('%b %Y')
#     except Exception:
#         period_start = None
#         period_end = None

#     parts = []
#     # Executive summary (bold)
#     if period_start and period_end:
#         parts.append(f"**Tổng doanh thu từ {period_start} đến {period_end} là ${total_sales:,.2f}**")
#     else:
#         parts.append(f"**Tổng doanh thu: ${total_sales:,.2f}**")

#     def b(x):
#         return f"**{x}**"

#     # Metrics summary
#     metrics = f"♦ {b('Tổng doanh thu')}: {b(f'${total_sales:,.2f}')} — {b('Tổng lợi nhuận')}: {b(f'${total_profit:,.2f}')} — {b('Số đơn hàng')}: {b(total_orders)}"
#     parts.append(metrics)

#     if max_month:
#         parts.append(f"♦ Doanh thu lớn nhất: {b(f'${max_month[1]:,.2f}')} vào {b(max_month[0])}")
#     if min_month:
#         parts.append(f"♦ Doanh thu nhỏ nhất: {b(f'${min_month[1]:,.2f}')} vào {b(min_month[0])}")

#     if recent_growth_pct is not None:
#         sign = '+' if recent_growth_pct >= 0 else ''
#         parts.append(f"♦ Tăng trưởng (đầu → cuối): {b(f'{sign}{recent_growth_pct:.1f}%')}")

#     if mom_max:
#         parts.append(f"♦ Tăng mạnh nhất theo tháng: {b(mom_max[0])} ({b(f'{mom_max[1]:+.1f}%')})")
#     if mom_min:
#         parts.append(f"♦ Giảm mạnh nhất theo tháng: {b(mom_min[0])} ({b(f'{mom_min[1]:+.1f}%')})")

#     parts.append(f"♦ Xu hướng hiện tại: {b(trend_text)}")

#     if forecast_summary:
#         last_actual = None
#         try:
#             if not df_trend.empty:
#                 df_month_tmp = df_trend.groupby([df_trend["Order Date"].dt.to_period("M")])["Sales"].sum().reset_index()
#                 df_month_tmp["Order Date"] = df_month_tmp["Order Date"].dt.to_timestamp()
#                 last_actual = float(df_month_tmp.iloc[-1]["Sales"])
#         except Exception:
#             last_actual = None

#         proj_parts = []
#         for ds, yhat in forecast_summary:
#             label = pd.to_datetime(ds).strftime('%b %Y') if ds else 'n/a'
#             pct = None
#             try:
#                 if last_actual and last_actual != 0:
#                     pct = (yhat - last_actual) / last_actual * 100
#             except Exception:
#                 pct = None
#             if pct is not None:
#                 proj_parts.append(f"{label}: {b(f'${yhat:,.2f}')} ({b(f'{pct:+.1f}%')})")
#             else:
#                 proj_parts.append(f"{label}: {b(f'${yhat:,.2f}')}")

#         parts.append(f"♦ Dự báo 3 tháng tới: {', '.join(proj_parts)}")

#     parts.append(f"♦ Gợi ý: {b('Xem xét A/B test cho thay đổi discount')} ở các nhóm có doanh thu cao.")

#     # Join into single-line format separated by ' - '
#     content = " - ".join(parts)

#     widgets = [
#         {
#             "widget_type": "insight",
#             "severity": "low",
#             "title": "Tổng quan hiệu suất",
#             "content_markdown": content,
#             "evidence_json": {"kpis": kpis, "sales_trend_sample": sales_trend[:6]},
#         }
#     ]

#     # Add a what-if widget if available
#     try:
#         if what_if and isinstance(what_if, dict) and what_if.get("discount_scenario"):
#             dw = what_if.get("discount_scenario", {})
#             widgets.append({
#                 "widget_type": "what_if",
#                 "severity": "medium",
#                 "title": "What-if: điều chỉnh discount",
#                 "content_markdown": (
#                     f"- Uớc tính thay đổi doanh thu: ${float(dw.get('uplift_sales', 0) or 0):,.2f}\n"
#                     f"- Uớc tính thay đổi lợi nhuận: ${float(dw.get('uplift_profit', 0) or 0):,.2f}"
#                 ),
#                 "evidence_json": {"what_if": dw},
#             })
#     except Exception:
#         pass

#     return widgets

def _default_widgets(evidence: dict):
    """Tạo insight với format giống hình ảnh: bullet • và xuống dòng rõ ràng"""
    kpis = evidence.get("kpis", {})
    what_if = evidence.get("what_if", {})
    forecast = evidence.get("forecast", [])
    sales_trend = evidence.get("sales_trend", [])

    total_sales = float(kpis.get("total_sales", 0) or 0)
    total_profit = float(kpis.get("total_profit", 0) or 0)
    total_orders = int(kpis.get("total_orders", 0) or 0)

    # Xử lý dữ liệu trend
    try:
        df_trend = pd.DataFrame(sales_trend)
        if not df_trend.empty and "Order Date" in df_trend.columns:
            df_trend["Order Date"] = pd.to_datetime(df_trend["Order Date"])
            df_trend = df_trend.sort_values("Order Date")

            df_month = df_trend.copy()
            df_month["Month"] = df_month["Order Date"].dt.to_period("M").dt.to_timestamp()
            df_month = df_month.groupby("Month")["Sales"].sum().reset_index()
            df_month = df_month.sort_values("Month")

            period_start = df_month["Month"].iloc[0].strftime('%b %Y')
            period_end = df_month["Month"].iloc[-1].strftime('%b %Y')

            max_row = df_month.loc[df_month["Sales"].idxmax()]
            min_row = df_month.loc[df_month["Sales"].idxmin()]
            max_month = (max_row["Month"].strftime("%b %Y"), float(max_row["Sales"]))
            min_month = (min_row["Month"].strftime("%b %Y"), float(min_row["Sales"]))

            first_sales = float(df_month.iloc[0]["Sales"])
            last_sales = float(df_month.iloc[-1]["Sales"])
            growth_pct = ((last_sales - first_sales) / first_sales * 100) if first_sales > 0 else 0

            df_month["pct_change"] = df_month["Sales"].pct_change() * 100
            mom_max_row = df_month.loc[df_month["pct_change"].idxmax()] if not df_month["pct_change"].dropna().empty else None
            mom_min_row = df_month.loc[df_month["pct_change"].idxmin()] if not df_month["pct_change"].dropna().empty else None

            mom_max = (mom_max_row["Month"].strftime("%b %Y"), float(mom_max_row["pct_change"])) if mom_max_row else None
            mom_min = (mom_min_row["Month"].strftime("%b %Y"), float(mom_min_row["pct_change"])) if mom_min_row else None

            trend_text = "tăng" if last_sales > first_sales else "giảm" if last_sales < first_sales else "ổn định"
        else:
            period_start = period_end = "N/A"
            max_month = min_month = mom_max = mom_min = None
            growth_pct = 0
            trend_text = "không rõ"
    except Exception:
        period_start = period_end = "N/A"
        max_month = min_month = mom_max = mom_min = None
        growth_pct = 0
        trend_text = "không rõ"

    # Dự báo
    forecast_lines = []
    try:
        if forecast and len(forecast) >= 3:
            for f in forecast[-3:]:
                ds = f.get("ds")
                yhat = float(f.get("yhat", 0) or 0)
                month_name = pd.to_datetime(ds).strftime('%b %Y') if ds else 'n/a'
                forecast_lines.append(f"{month_name}: **${yhat:,.2f}**")
    except Exception:
        forecast_lines = []

    # Xây dựng nội dung với xuống dòng rõ ràng
    lines = []
    lines.append(f"**Tổng doanh thu từ {period_start} đến {period_end} là ${total_sales:,.2f}**")
    lines.append("")  # xuống dòng
    lines.append(f"• Tổng doanh thu: **${total_sales:,.2f}** — Tổng lợi nhuận: **${total_profit:,.2f}** — Số đơn hàng: **{total_orders}**")

    if max_month:
        lines.append(f"• Doanh thu lớn nhất: **${max_month[1]:,.2f}** được ghi nhận vào **{max_month[0]}**")
    if min_month:
        lines.append(f"• Doanh thu nhỏ nhất: **${min_month[1]:,.2f}** được ghi nhận vào **{min_month[0]}**")

    sign = '+' if growth_pct >= 0 else ''
    lines.append(f"• Tăng trưởng (đầu → cuối): **{sign}{growth_pct:.1f}%**")

    if mom_max:
        lines.append(f"• Tăng mạnh nhất theo tháng: **{mom_max[0]}** (**{mom_max[1]:+.1f}%**)")
    if mom_min:
        lines.append(f"• Giảm mạnh nhất theo tháng: **{mom_min[0]}** (**{mom_min[1]:+.1f}%**)")

    lines.append(f"• Xu hướng hiện tại: **{trend_text}**")

    if forecast_lines:
        lines.append(f"• Dự báo 3 tháng tới: {', '.join(forecast_lines)}")

    lines.append("• Gợi ý: Xem xét **A/B test thay đổi discount** tại các nhóm sản phẩm có doanh thu cao để tối ưu lợi nhuận.")

    content_markdown = "\n".join(lines)

    widgets = [
        {
            "widget_type": "insight",
            "severity": "low",
            "title": "Tổng quan hiệu suất kinh doanh",
            "content_markdown": content_markdown,
            "evidence_json": {"kpis": kpis, "period": f"{period_start} - {period_end}"}
        }
    ]

    # What-if widget
    try:
        if what_if and what_if.get("discount_scenario"):
            dw = what_if["discount_scenario"]
            widgets.append({
                "widget_type": "what_if",
                "severity": "medium",
                "title": "What-if: Điều chỉnh discount",
                "content_markdown": (
                    f"• Ước tính tăng doanh thu: **${float(dw.get('uplift_sales', 0) or 0):,.2f}**\n"
                    f"• Ước tính tăng lợi nhuận: **${float(dw.get('uplift_profit', 0) or 0):,.2f}**"
                ),
                "evidence_json": {"what_if": dw},
            })
    except Exception:
        pass

    return widgets


import hashlib
import time
import json
import uuid
import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

AI_INSIGHT_FEATURE_ENABLED = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))
AI_INSIGHT_MODEL_TIMEOUT_SECONDS = float(os.getenv("AI_INSIGHT_MODEL_TIMEOUT_SECONDS", "8.0"))
AI_INSIGHT_RATE_LIMIT = "10/minute"
AI_INSIGHT_CACHE_TTL_SECONDS = int(os.getenv("AI_INSIGHT_CACHE_TTL_SECONDS", "1800"))

_chart_insight_cache = {}
_chart_insight_jobs = {}
_chart_insight_feedback = {}
_chart_insight_executor = ThreadPoolExecutor(max_workers=int(os.getenv("AI_INSIGHT_WORKERS", "4")))

def _now_ms():
    return int(time.time() * 1000)

class ChartSelectionPoint(BaseModel):
    x: Optional[str] = None
    y: Optional[float] = None
    label: Optional[str] = None
    timestamp: Optional[str] = None

class ChartSelectionRange(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None

class ChartSelection(BaseModel):
    point: Optional[ChartSelectionPoint] = None
    range: Optional[ChartSelectionRange] = None

class ChartAggregates(BaseModel):
    sum: Optional[float] = None
    mean: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    stddev: Optional[float] = None
    pct_change: Optional[float] = None
    slope: Optional[float] = None

class ChartInsightRequest(BaseModel):
    chartId: str
    chartType: str
    selection: Optional[ChartSelection] = None
    aggregates: Optional[ChartAggregates] = None
    filters: dict = {}
    timeRange: Optional[dict] = None
    detailLevel: str = "short"
    locale: str = "vi"
    context: Optional[str] = None

class ChatRequest(BaseModel):
    analysis_run_id: str
    message: str

class ExplanationInfo(BaseModel):
    text: str
    metric_reference: Optional[str] = None

class ChartInsightResponse(BaseModel):
    id: str
    summary: str
    highlights: List[str]
    explanations: List[ExplanationInfo]
    actions: List[str]
    confidence: float
    model_meta: dict
    cached: bool = False
    status: str = "succeeded"

def _coerce_for_json(value):
    if isinstance(value, dict):
        return {k: _coerce_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_for_json(v) for v in value]
    if pd.isna(value):
        return None
    try:
        import numpy as np
        if isinstance(value, np.generic):
            return value.item()
    except ImportError:
        pass
    if isinstance(value, (pd.Timestamp, datetime.datetime)):
        return value.isoformat()
    return value

def _sanitize_for_llm(data: dict) -> dict:
    return {k: v for k, v in data.items() if not k.lower() in ["password", "token", "secret", "user_id"]}

def _fingerprint_chart_request(payload: dict) -> str:
    s = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _generate_chart_insight_via_llm(req: ChartInsightRequest) -> ChartInsightResponse:
    job_id = str(uuid.uuid4())
    client = _get_openai_client()
    if not client:
        return _fallback_chart_insight(req)

    model_name = os.getenv("OPENROUTER_MODEL") or os.getenv("OPENAI_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    start_time = time.time()
    
    context_str = req.context or ""
    filters_str = json.dumps(_sanitize_for_llm(req.filters), ensure_ascii=False)
    agg_str = json.dumps(_coerce_for_json(req.aggregates.model_dump()) if req.aggregates else {}, ensure_ascii=False)
    sel_str = json.dumps(_coerce_for_json(req.selection.model_dump()) if req.selection else {}, ensure_ascii=False)

    system_prompt = f"""
Bạn là chuyên gia phân tích dữ liệu kinh doanh (BI Analyst).
Nhiệm vụ: phân tích dữ liệu chart click từ người dùng và đưa ra insight cụ thể.
Chart ID: {req.chartId} ({req.chartType})
Filters: {filters_str}
Aggregates: {agg_str}
Selection: {sel_str}
DetailLevel: {req.detailLevel}
Context: {context_str}

QUY TẮC BẮT BUỘC:
1. Dựa vào aggregates và selection để đưa ra summary ngắn gọn, tập trung vào thay đổi quan trọng.
2. highlights: 2-3 ý chính (sử dụng cụ thể số liệu).
3. actions: đề xuất hành động kinh doanh phù hợp.
4. Dùng tiếng {"Việt" if req.locale == "vi" else "Anh"}.
5. Return FORMAT: valid JSON ONLY matching the Schema: {{"summary": "...", "highlights": [], "explanations": [{{"text": "...", "metric_reference": "..."}}], "actions": [], "confidence": 0.85}}
"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Tạo insight format JSON."}
            ],
            response_format={"type": "json_object"}
        )
        latency = int((time.time() - start_time) * 1000)
        parsed = json.loads(response.choices[0].message.content)
        
        explanations = parsed.get("explanations", [])
        if "explanations" in parsed and all(isinstance(x, str) for x in explanations):
             explanations = [{"text": x, "metric_reference": None} for x in explanations]

        return ChartInsightResponse(
            id=job_id,
            summary=parsed.get("summary", ""),
            highlights=parsed.get("highlights", []),
            explanations=[ExplanationInfo(**e) if isinstance(e, dict) else ExplanationInfo(text=str(e), metric_reference=None) for e in explanations],
            actions=parsed.get("actions", []),
            confidence=float(parsed.get("confidence", 0.8)),
            model_meta={"model_name": model_name, "latency_ms": latency}
        )
    except Exception as e:
        logger.error(f"LLM Insight Error: {e}")
        return _fallback_chart_insight(req)

def _fallback_chart_insight(req: ChartInsightRequest) -> ChartInsightResponse:
    job_id = str(uuid.uuid4())
    agg = req.aggregates
    v_sum = agg.sum if agg else None
    v_mean = agg.mean if agg else None
    v_min = agg.min if agg else None
    v_max = agg.max if agg else None
    
    return ChartInsightResponse(
        id=job_id,
        summary=f"Tóm tắt nhanh cho `{req.chartId}` dựa trên aggregates." if req.locale=="vi" else f"Quick summary for `{req.chartId}`.",
        highlights=[
            f"Tổng: {'N/A' if v_sum is None else round(v_sum,2)}",
            f"Min–Max: {'N/A' if v_min is None else round(v_min,2)} → {'N/A' if v_max is None else round(v_max,2)}",
            f"Trung bình: {'N/A' if v_mean is None else round(v_mean,2)}"
        ],
        explanations=[ExplanationInfo(text="Insight được suy ra từ aggregates." if req.locale=="vi" else "Insight derived from client aggregates.", metric_reference=None)],
        actions=["Kiểm tra các điểm bất thường gần đây." if req.locale=="vi" else "Check recent anomalies."],
        confidence=0.55,
        model_meta={"model_name": "rule_based_fallback", "latency_ms": 0}
    )

@app.post("/api/ai/insights")
@limiter.limit(AI_INSIGHT_RATE_LIMIT)
def generate_ai_insights(
    request: Request,
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    if not AI_INSIGHT_FEATURE_ENABLED:
        raise HTTPException(status_code=503, detail="AI insight feature is disabled")

    req_obj = ChartInsightRequest.model_validate(payload)
    fp_payload = {
        "chartId": req_obj.chartId,
        "chartType": req_obj.chartType,
        "selection": _coerce_for_json(req_obj.selection.model_dump() if req_obj.selection else None),
        "aggregates": _coerce_for_json(req_obj.aggregates.model_dump() if req_obj.aggregates else None),
        "filters": _sanitize_for_llm(req_obj.filters or {}),
        "timeRange": req_obj.timeRange,
        "detailLevel": req_obj.detailLevel,
        "locale": req_obj.locale,
        "context": req_obj.context,
    }
    fp = _fingerprint_chart_request(fp_payload)
    now = time.time()

    cached_entry = _chart_insight_cache.get(fp)
    if cached_entry and cached_entry.get("expires_at", 0) > now:
        cached_resp = cached_entry["value"]
        cached_resp["cached"] = True
        return cached_resp

    job = _chart_insight_jobs.get(fp)
    if job and job.get("status") == "processing":
        return {
            "id": job["id"],
            "summary": "Insight đang được xử lý." if (req_obj.locale or "vi").lower().startswith("vi") else "Insight is being generated.",
            "highlights": [],
            "explanations": [],
            "actions": [],
            "confidence": 0.0,
            "model_meta": {"model_name": job.get("model_name", "unknown"), "latency_ms": job.get("latency_ms", 0)},
            "cached": False,
            "status": "processing",
        }

    job_id = str(uuid.uuid4())
    _chart_insight_jobs[fp] = {"id": job_id, "status": "processing", "started_at_ms": _now_ms()}

    future = _chart_insight_executor.submit(_generate_chart_insight_via_llm, req_obj)
    try:
        resp_obj = future.result(timeout=AI_INSIGHT_MODEL_TIMEOUT_SECONDS)
        resp = resp_obj.model_dump()
        resp["cached"] = False
        resp["status"] = "succeeded"
        _chart_insight_cache[fp] = {"expires_at": now + AI_INSIGHT_CACHE_TTL_SECONDS, "value": resp}
        _chart_insight_jobs[fp] = {"id": resp["id"], "status": "succeeded", "completed_at_ms": _now_ms(), "fingerprint": fp}
        return resp
    except FuturesTimeoutError:
        _chart_insight_jobs[fp].update({"id": job_id, "status": "processing", "future": future})
        return {
            "id": job_id,
            "summary": "Insight đang được xử lý." if (req_obj.locale or "vi").lower().startswith("vi") else "Insight is being generated.",
            "highlights": [],
            "explanations": [],
            "actions": [],
            "confidence": 0.0,
            "model_meta": {"model_name": "pending", "latency_ms": int(AI_INSIGHT_MODEL_TIMEOUT_SECONDS * 1000)},
            "cached": False,
            "status": "processing",
        }

@app.get("/api/ai/insights/{insight_id}")
@limiter.limit(AI_INSIGHT_RATE_LIMIT)
def get_ai_insight(insight_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    if not AI_INSIGHT_FEATURE_ENABLED:
        raise HTTPException(status_code=503, detail="AI insight feature is disabled")

    for fp, job in _chart_insight_jobs.items():
        if job.get("id") != insight_id:
            continue

        if job.get("status") == "succeeded":
            cached = _chart_insight_cache.get(fp)
            if cached and cached.get("expires_at", 0) > time.time():
                resp = dict(cached["value"])
                resp["cached"] = True
                return resp
            return {"id": insight_id, "status": "succeeded"}

        if job.get("status") == "failed":
            raise HTTPException(status_code=500, detail="Insight generation failed")

        future = job.get("future")
        if future is None:
            return {"id": insight_id, "status": "processing"}

        if future.done():
            try:
                resp_obj = future.result()
                resp = resp_obj.model_dump()
                resp["cached"] = False
                resp["status"] = "succeeded"
                _chart_insight_cache[fp] = {"expires_at": time.time() + AI_INSIGHT_CACHE_TTL_SECONDS, "value": resp}
                _chart_insight_jobs[fp] = {"id": resp["id"], "status": "succeeded", "completed_at_ms": _now_ms(), "fingerprint": fp}
                return resp
            except Exception as exc:
                _chart_insight_jobs[fp] = {"id": insight_id, "status": "failed", "error": str(exc)}
                raise HTTPException(status_code=500, detail="Insight generation failed")

        return {"id": insight_id, "status": "processing"}

    raise HTTPException(status_code=404, detail="Insight not found")

@app.post("/api/ai/insights/{insight_id}/feedback")
@limiter.limit(AI_INSIGHT_RATE_LIMIT)
def submit_ai_insight_feedback(insight_id: str, request: Request, payload: dict, current_user: dict = Depends(get_current_user)):
    useful = bool(payload.get("useful"))
    comment = payload.get("comment")
    user_key = (current_user or {}).get("username") or "anonymous"

    _chart_insight_feedback.setdefault(insight_id, []).append(
        {
            "useful": useful,
            "comment": comment,
            "user": user_key,
            "ts": datetime.datetime.utcnow().isoformat(),
        }
    )
    return {"ok": True}


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

class FiltersPayload(BaseModel):
    category: Optional[List[str]] = None
    region: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class AnalysisInsightRequest(BaseModel):
    analysis_run_id: str


class ChatRequest(BaseModel):
    analysis_run_id: str
    message: str


def _get_openai_client():
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    base_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.io/api/v1").rstrip("/")

    if OpenAI is not None:
        try:
            return OpenAI(api_key=api_key, base_url=base_url)
        except Exception:
            pass

    class _SimpleCompletions:
        def __init__(self, api_key, base_url):
            self.api_key = api_key
            self.base_url = base_url

        def create(self, model, temperature=0.7, response_format=None, messages=None, max_tokens=512, **kwargs):
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": model,
                "messages": messages or [],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            class _Msg:
                def __init__(self, content):
                    self.message = type("_", (), {"content": content})

            choices = []
            if isinstance(data, dict) and "choices" in data and len(data["choices"]) > 0:
                first = data["choices"][0]
                content = None
                if isinstance(first, dict):
                    content = first.get("message", {}).get("content") if first.get("message") else first.get("text")
                else:
                    content = str(first)
                choices = [_Msg(content)]
            else:
                choices = [_Msg(json.dumps(data, ensure_ascii=False))]

            return type("_", (), {"choices": choices})

    class _SimpleChat:
        def __init__(self, api_key, base_url):
            self.completions = _SimpleCompletions(api_key, base_url)

    class _SimpleClient:
        def __init__(self, api_key, base_url):
            self.chat = _SimpleChat(api_key, base_url)

    return _SimpleClient(api_key, base_url)


def _coerce_for_json(value):
    if isinstance(value, (np.generic,)):
        return value.item()
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, dict):
        return {k: _coerce_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_for_json(v) for v in value]
    return value


def _compute_analysis_bundle(filters: FiltersPayload):
    try:
        df = load_data()
        logger.info(f"load_data thành công: {len(df)} records, columns: {df.columns.tolist()}")
    except Exception as e:
        logger.error(f"load_data thất bại: {e}")
        df = pd.DataFrame()

    try:
        filtered = apply_filters(
            df,
            filters.category,
            filters.region,
            filters.start_date,
            filters.end_date,
        )
    except Exception as e:
        logger.warning(f"apply_filters lỗi: {e}")
        filtered = pd.DataFrame()

    if filtered.empty:
        logger.warning("Dữ liệu sau filter rỗng → trả về bundle mặc định")
        return {
            "kpis": {"total_sales": 0, "total_profit": 0, "total_orders": 0, "avg_discount": 0},
            "sales_trend": [],
            "category_sales": [],
            "region_sales": [],
            "forecast": [],
            "rfm": {"segments": [], "customers": []},
            "what_if": {
                "discount_scenario": {"delta_discount_pct": 1.0, "uplift_sales": 0, "uplift_profit": 0},
                "at_risk_scenario": {"conversion_rate": 0.1, "uplift_sales": 0, "uplift_profit": 0},
            },
        }

    try:
        kpis = {
            "total_sales": float(filtered["Sales"].sum()),
            "total_profit": float(filtered["Profit"].sum()),
            "total_orders": int(filtered["Order ID"].nunique()),
            "avg_discount": float(filtered["Discount"].mean()),
        }
    except Exception as e:
        logger.warning(f"Tính KPI lỗi: {e}")
        kpis = {"total_sales": 0, "total_profit": 0, "total_orders": 0, "avg_discount": 0}

    try:
        sales_trend = filtered.groupby("Order Date")["Sales"].sum().reset_index()
        sales_trend["Order Date"] = sales_trend["Order Date"].dt.strftime('%Y-%m-%d')
        sales_trend = sales_trend.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"Sales trend lỗi: {e}")
        sales_trend = []

    try:
        category_sales = filtered.groupby("Category")["Sales"].sum().sort_values(ascending=False).reset_index().to_dict(orient="records")
        region_sales = filtered.groupby("Region")["Sales"].sum().reset_index().to_dict(orient="records")
    except Exception as e:
        logger.warning(f"Category/Region sales lỗi: {e}")
        category_sales = []
        region_sales = []

    forecast_data = []
    try:
        sales_df = filtered[["Order Date", "Sales"]].rename(columns={"Order Date": "ds", "Sales": "y"}).groupby("ds").sum().reset_index()
        if len(sales_df) >= 50:
            model = Prophet(interval_width=0.95)
            model.fit(sales_df)
            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)
            forecast_data = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(60)
            forecast_data["ds"] = forecast_data["ds"].dt.strftime('%Y-%m-%d')
            forecast_data = forecast_data.to_dict(orient="records")
    except Exception as e:
        logger.warning(f"Forecast lỗi: {e}")

    try:
        reference_date = filtered["Order Date"].max()
        rfm = filtered.groupby("Customer ID").agg({
            "Order Date": lambda x: (reference_date - x.max()).days,
            "Order ID": "count",
            "Sales": "sum",
        }).reset_index()
        rfm.columns = ["Customer ID", "Recency", "Frequency", "Monetary"]

        customer_names = filtered[["Customer ID", "Customer Name"]].drop_duplicates()
        rfm = rfm.merge(customer_names, on="Customer ID", how="left")

        if len(rfm) >= 4:
            scaler = StandardScaler()
            rfm_scaled = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])
            kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
            rfm["Cluster"] = kmeans.fit_predict(rfm_scaled)

            cluster_stats = rfm.groupby("Cluster").agg({"Recency": "mean", "Frequency": "mean", "Monetary": "mean"})

            def _segment_label(cluster_id):
                recency_rank = cluster_stats["Recency"].rank()[cluster_id]
                frequency_rank = cluster_stats["Frequency"].rank()[cluster_id]
                monetary_rank = cluster_stats["Monetary"].rank()[cluster_id]
                if frequency_rank >= 3 and monetary_rank >= 3:
                    return "Champions"
                if recency_rank >= 3:
                    return "At Risk"
                if frequency_rank <= 2 and monetary_rank <= 2:
                    return "New Customers"
                return "Loyal"

            rfm["Segment"] = rfm["Cluster"].apply(_segment_label)
        else:
            rfm["Segment"] = "Unclassified"

        segment_summary = rfm.groupby("Segment").agg({
            "Customer ID": "count",
            "Recency": "mean",
            "Frequency": "mean",
            "Monetary": "mean",
        }).reset_index()
        segment_summary.columns = ["segment", "customer_count", "avg_recency", "avg_frequency", "avg_monetary"]

        rfm_result = {
            "segments": segment_summary.to_dict(orient="records"),
            "customers": rfm[["Customer ID", "Customer Name", "Recency", "Frequency", "Monetary", "Segment"]].to_dict(orient="records"),
        }
    except Exception as e:
        logger.warning(f"RFM segmentation lỗi: {e}")
        rfm_result = {"segments": [], "customers": []}

    try:
        margin = (kpis["total_profit"] / kpis["total_sales"]) if kpis["total_sales"] > 0 else 0
        discount_sensitivity = float(np.nan_to_num(filtered[["Discount", "Sales"]].corr().iloc[0, 1], nan=0.0))
        delta_discount_pct = 1.0
        uplift_sales = kpis["total_sales"] * (discount_sensitivity * (delta_discount_pct / 100))
        uplift_profit = uplift_sales * margin

        at_risk_segment = next((s for s in rfm_result["segments"] if s["segment"] == "At Risk"), None)
        total_customers = max(sum(int(s["customer_count"]) for s in rfm_result["segments"]), 1)
        at_risk_share = (at_risk_segment["customer_count"] / total_customers) if at_risk_segment else 0
        conversion_rate = 0.1
        avg_monetary_at_risk = at_risk_segment["avg_monetary"] if at_risk_segment else 0
        uplift_sales_at_risk = float(avg_monetary_at_risk) * conversion_rate * float(at_risk_share)

        what_if = {
            "discount_scenario": {
                "delta_discount_pct": delta_discount_pct,
                "discount_sensitivity": discount_sensitivity,
                "margin_assumption": margin,
                "uplift_sales": float(uplift_sales),
                "uplift_profit": float(uplift_profit),
            },
            "at_risk_scenario": {
                "conversion_rate": conversion_rate,
                "at_risk_share": float(at_risk_share),
                "avg_monetary_at_risk": float(avg_monetary_at_risk),
                "uplift_sales": float(uplift_sales_at_risk),
                "uplift_profit": float(uplift_sales_at_risk * margin),
            },
        }
    except Exception as e:
        logger.warning(f"What-if calculation lỗi: {e}")
        what_if = {"discount_scenario": {}, "at_risk_scenario": {}}

    return {
        "kpis": kpis,
        "sales_trend": sales_trend,
        "category_sales": category_sales,
        "region_sales": region_sales,
        "forecast": forecast_data,
        "rfm": rfm_result,
        "what_if": what_if,
    }


# def _default_widgets(evidence: dict):
#     # Build richer Vietnamese insights using available evidence
#     kpis = evidence.get("kpis", {})
#     what_if = evidence.get("what_if", {})
#     forecast = evidence.get("forecast", [])
#     sales_trend = evidence.get("sales_trend", [])

#     total_sales = float(kpis.get("total_sales", 0) or 0)
#     total_profit = float(kpis.get("total_profit", 0) or 0)
#     total_orders = int(kpis.get("total_orders", 0) or 0)

#     # Prepare sales trend DataFrame if available
#     try:
#         df_trend = pd.DataFrame(sales_trend)
#         if not df_trend.empty and "Order Date" in df_trend.columns:
#             df_trend["Order Date"] = pd.to_datetime(df_trend["Order Date"])
#             df_trend = df_trend.sort_values("Order Date")
#             df_trend["year"] = df_trend["Order Date"].dt.year
#             df_trend["month"] = df_trend["Order Date"].dt.month
#             df_trend["month_label"] = df_trend["Order Date"].dt.strftime("%m/%Y")
#         else:
#             df_trend = pd.DataFrame()
#     except Exception:
#         df_trend = pd.DataFrame()

#     # Compute notable points
#     max_month = None
#     min_month = None
#     recent_growth_pct = None
#     mom_max = None
#     mom_min = None
#     trend_text = "không rõ"

#     try:
#         if not df_trend.empty:
#             # aggregate by month
#             df_month = df_trend.copy()
#             df_month = df_month.groupby([df_month["Order Date"].dt.to_period("M")])["Sales"].sum().reset_index()
#             df_month["Order Date"] = df_month["Order Date"].dt.to_timestamp()
#             df_month = df_month.sort_values("Order Date")

#             max_row = df_month.loc[df_month["Sales"].idxmax()]
#             min_row = df_month.loc[df_month["Sales"].idxmin()]
#             max_month = (max_row["Order Date"].strftime("%b %Y"), float(max_row["Sales"]))
#             min_month = (min_row["Order Date"].strftime("%b %Y"), float(min_row["Sales"]))

#             # Recent growth: compare last month vs first month in the series
#             first = df_month.iloc[0]["Sales"]
#             last = df_month.iloc[-1]["Sales"]
#             if first and not np.isclose(first, 0):
#                 recent_growth_pct = (last - first) / first * 100
#             else:
#                 recent_growth_pct = None

#             # month-over-month changes
#             df_month["pct_change"] = df_month["Sales"].pct_change() * 100
#             if df_month["pct_change"].dropna().size:
#                 mom_max_row = df_month.loc[df_month["pct_change"].idxmax()]
#                 mom_min_row = df_month.loc[df_month["pct_change"].idxmin()]
#                 mom_max = (mom_max_row["Order Date"].strftime("%b %Y"), float(mom_max_row["pct_change"]))
#                 mom_min = (mom_min_row["Order Date"].strftime("%b %Y"), float(mom_min_row["pct_change"]))

#             # Trend: simple linear fit on months
#             try:
#                 xs = np.arange(len(df_month))
#                 ys = df_month["Sales"].values.astype(float)
#                 if len(xs) > 1 and not np.allclose(ys, ys[0]):
#                     slope = np.polyfit(xs, ys, 1)[0]
#                     trend_text = "tăng" if slope > 0 else "giảm" if slope < 0 else "ổn định"
#             except Exception:
#                 pass
#     except Exception:
#         pass

#     # Forecast summary (next 3 points if available)
#     forecast_summary = []
#     try:
#         if forecast and isinstance(forecast, list):
#             last_three = forecast[-3:]
#             for f in last_three:
#                 ds = f.get("ds")
#                 yhat = float(f.get("yhat", 0) or 0)
#                 forecast_summary.append((ds, yhat))
#     except Exception:
#         forecast_summary = []

#     # Compose Vietnamese markdown matching the example: bold summary + bullet insights
#     period_start = None
#     period_end = None
#     try:
#         if not df_trend.empty:
#             period_start = df_trend["Order Date"].iloc[0].strftime('%b %Y')
#             period_end = df_trend["Order Date"].iloc[-1].strftime('%b %Y')
#     except Exception:
#         period_start = None
#         period_end = None

#     parts = []
#     # Executive summary (bold)
#     if period_start and period_end:
#         parts.append(f"**Tổng doanh thu từ {period_start} đến {period_end} là ${total_sales:,.2f}**")
#     else:
#         parts.append(f"**Tổng doanh thu: ${total_sales:,.2f}**")

#     def b(x):
#         return f"**{x}**"

#     # Metrics summary
#     metrics = f"♦ {b('Tổng doanh thu')}: {b(f'${total_sales:,.2f}')} — {b('Tổng lợi nhuận')}: {b(f'${total_profit:,.2f}')} — {b('Số đơn hàng')}: {b(total_orders)}"
#     parts.append(metrics)

#     if max_month:
#         parts.append(f"♦ Doanh thu lớn nhất: {b(f'${max_month[1]:,.2f}')} vào {b(max_month[0])}")
#     if min_month:
#         parts.append(f"♦ Doanh thu nhỏ nhất: {b(f'${min_month[1]:,.2f}')} vào {b(min_month[0])}")

#     if recent_growth_pct is not None:
#         sign = '+' if recent_growth_pct >= 0 else ''
#         parts.append(f"♦ Tăng trưởng (đầu → cuối): {b(f'{sign}{recent_growth_pct:.1f}%')}")

#     if mom_max:
#         parts.append(f"♦ Tăng mạnh nhất theo tháng: {b(mom_max[0])} ({b(f'{mom_max[1]:+.1f}%')})")
#     if mom_min:
#         parts.append(f"♦ Giảm mạnh nhất theo tháng: {b(mom_min[0])} ({b(f'{mom_min[1]:+.1f}%')})")

#     parts.append(f"♦ Xu hướng hiện tại: {b(trend_text)}")

#     if forecast_summary:
#         last_actual = None
#         try:
#             if not df_trend.empty:
#                 df_month_tmp = df_trend.groupby([df_trend["Order Date"].dt.to_period("M")])["Sales"].sum().reset_index()
#                 df_month_tmp["Order Date"] = df_month_tmp["Order Date"].dt.to_timestamp()
#                 last_actual = float(df_month_tmp.iloc[-1]["Sales"])
#         except Exception:
#             last_actual = None

#         proj_parts = []
#         for ds, yhat in forecast_summary:
#             label = pd.to_datetime(ds).strftime('%b %Y') if ds else 'n/a'
#             pct = None
#             try:
#                 if last_actual and last_actual != 0:
#                     pct = (yhat - last_actual) / last_actual * 100
#             except Exception:
#                 pct = None
#             if pct is not None:
#                 proj_parts.append(f"{label}: {b(f'${yhat:,.2f}')} ({b(f'{pct:+.1f}%')})")
#             else:
#                 proj_parts.append(f"{label}: {b(f'${yhat:,.2f}')}")

#         parts.append(f"♦ Dự báo 3 tháng tới: {', '.join(proj_parts)}")

#     parts.append(f"♦ Gợi ý: {b('Xem xét A/B test cho thay đổi discount')} ở các nhóm có doanh thu cao.")

#     # Join into single-line format separated by ' - '
#     content = " - ".join(parts)

#     widgets = [
#         {
#             "widget_type": "insight",
#             "severity": "low",
#             "title": "Tổng quan hiệu suất",
#             "content_markdown": content,
#             "evidence_json": {"kpis": kpis, "sales_trend_sample": sales_trend[:6]},
#         }
#     ]

#     # Add a what-if widget if available
#     try:
#         if what_if and isinstance(what_if, dict) and what_if.get("discount_scenario"):
#             dw = what_if.get("discount_scenario", {})
#             widgets.append({
#                 "widget_type": "what_if",
#                 "severity": "medium",
#                 "title": "What-if: điều chỉnh discount",
#                 "content_markdown": (
#                     f"- Uớc tính thay đổi doanh thu: ${float(dw.get('uplift_sales', 0) or 0):,.2f}\n"
#                     f"- Uớc tính thay đổi lợi nhuận: ${float(dw.get('uplift_profit', 0) or 0):,.2f}"
#                 ),
#                 "evidence_json": {"what_if": dw},
#             })
#     except Exception:
#         pass

#     return widgets

def _default_widgets(evidence: dict):
    """Tạo insight với format giống hình ảnh: bullet • và xuống dòng rõ ràng"""
    kpis = evidence.get("kpis", {})
    what_if = evidence.get("what_if", {})
    forecast = evidence.get("forecast", [])
    sales_trend = evidence.get("sales_trend", [])

    total_sales = float(kpis.get("total_sales", 0) or 0)
    total_profit = float(kpis.get("total_profit", 0) or 0)
    total_orders = int(kpis.get("total_orders", 0) or 0)

    # Xử lý dữ liệu trend
    try:
        df_trend = pd.DataFrame(sales_trend)
        if not df_trend.empty and "Order Date" in df_trend.columns:
            df_trend["Order Date"] = pd.to_datetime(df_trend["Order Date"])
            df_trend = df_trend.sort_values("Order Date")

            df_month = df_trend.copy()
            df_month["Month"] = df_month["Order Date"].dt.to_period("M").dt.to_timestamp()
            df_month = df_month.groupby("Month")["Sales"].sum().reset_index()
            df_month = df_month.sort_values("Month")

            period_start = df_month["Month"].iloc[0].strftime('%b %Y')
            period_end = df_month["Month"].iloc[-1].strftime('%b %Y')

            max_row = df_month.loc[df_month["Sales"].idxmax()]
            min_row = df_month.loc[df_month["Sales"].idxmin()]
            max_month = (max_row["Month"].strftime("%b %Y"), float(max_row["Sales"]))
            min_month = (min_row["Month"].strftime("%b %Y"), float(min_row["Sales"]))

            first_sales = float(df_month.iloc[0]["Sales"])
            last_sales = float(df_month.iloc[-1]["Sales"])
            growth_pct = ((last_sales - first_sales) / first_sales * 100) if first_sales > 0 else 0

            df_month["pct_change"] = df_month["Sales"].pct_change() * 100
            mom_max_row = df_month.loc[df_month["pct_change"].idxmax()] if not df_month["pct_change"].dropna().empty else None
            mom_min_row = df_month.loc[df_month["pct_change"].idxmin()] if not df_month["pct_change"].dropna().empty else None

            mom_max = (mom_max_row["Month"].strftime("%b %Y"), float(mom_max_row["pct_change"])) if mom_max_row else None
            mom_min = (mom_min_row["Month"].strftime("%b %Y"), float(mom_min_row["pct_change"])) if mom_min_row else None

            trend_text = "tăng" if last_sales > first_sales else "giảm" if last_sales < first_sales else "ổn định"
        else:
            period_start = period_end = "N/A"
            max_month = min_month = mom_max = mom_min = None
            growth_pct = 0
            trend_text = "không rõ"
    except Exception:
        period_start = period_end = "N/A"
        max_month = min_month = mom_max = mom_min = None
        growth_pct = 0
        trend_text = "không rõ"

    # Dự báo
    forecast_lines = []
    try:
        if forecast and len(forecast) >= 3:
            for f in forecast[-3:]:
                ds = f.get("ds")
                yhat = float(f.get("yhat", 0) or 0)
                month_name = pd.to_datetime(ds).strftime('%b %Y') if ds else 'n/a'
                forecast_lines.append(f"{month_name}: **${yhat:,.2f}**")
    except Exception:
        forecast_lines = []

    # Xây dựng nội dung với xuống dòng rõ ràng
    lines = []
    lines.append(f"**Tổng doanh thu từ {period_start} đến {period_end} là ${total_sales:,.2f}**")
    lines.append("")  # xuống dòng
    lines.append(f"• Tổng doanh thu: **${total_sales:,.2f}** — Tổng lợi nhuận: **${total_profit:,.2f}** — Số đơn hàng: **{total_orders}**")

    if max_month:
        lines.append(f"• Doanh thu lớn nhất: **${max_month[1]:,.2f}** được ghi nhận vào **{max_month[0]}**")
    if min_month:
        lines.append(f"• Doanh thu nhỏ nhất: **${min_month[1]:,.2f}** được ghi nhận vào **{min_month[0]}**")

    sign = '+' if growth_pct >= 0 else ''
    lines.append(f"• Tăng trưởng (đầu → cuối): **{sign}{growth_pct:.1f}%**")

    if mom_max:
        lines.append(f"• Tăng mạnh nhất theo tháng: **{mom_max[0]}** (**{mom_max[1]:+.1f}%**)")
    if mom_min:
        lines.append(f"• Giảm mạnh nhất theo tháng: **{mom_min[0]}** (**{mom_min[1]:+.1f}%**)")

    lines.append(f"• Xu hướng hiện tại: **{trend_text}**")

    if forecast_lines:
        lines.append(f"• Dự báo 3 tháng tới: {', '.join(forecast_lines)}")

    lines.append("• Gợi ý: Xem xét **A/B test thay đổi discount** tại các nhóm sản phẩm có doanh thu cao để tối ưu lợi nhuận.")

    content_markdown = "\n".join(lines)

    widgets = [
        {
            "widget_type": "insight",
            "severity": "low",
            "title": "Tổng quan hiệu suất kinh doanh",
            "content_markdown": content_markdown,
            "evidence_json": {"kpis": kpis, "period": f"{period_start} - {period_end}"}
        }
    ]

    # What-if widget
    try:
        if what_if and what_if.get("discount_scenario"):
            dw = what_if["discount_scenario"]
            widgets.append({
                "widget_type": "what_if",
                "severity": "medium",
                "title": "What-if: Điều chỉnh discount",
                "content_markdown": (
                    f"• Ước tính tăng doanh thu: **${float(dw.get('uplift_sales', 0) or 0):,.2f}**\n"
                    f"• Ước tính tăng lợi nhuận: **${float(dw.get('uplift_profit', 0) or 0):,.2f}**"
                ),
                "evidence_json": {"what_if": dw},
            })
    except Exception:
        pass

    return widgets


@app.post("/api/ai/insights")
@limiter.limit("20/minute")
def generate_ai_insights(request: Request, payload: dict, current_user: dict = Depends(get_current_user)):
    # Support both analysis-run insights and chart-level requests
    try:
        if payload.get("analysis_run_id"):
            # Analysis-run based insights
            req = AnalysisInsightRequest(**payload)
            if not is_db_enabled():
                raise HTTPException(status_code=503, detail="PostgreSQL is required for AI insights")
            analysis_run = get_analysis_run(req.analysis_run_id)
            if not analysis_run:
                raise HTTPException(status_code=404, detail="Analysis run not found")

            dataset_id = analysis_run.get("dataset_id")

            evidence = {
                "kpis": analysis_run.get("computed_kpis_json", {}),
                "sales_trend": analysis_run.get("sales_trend_json", []),
                "category_sales": analysis_run.get("category_sales_json", []),
                "region_sales": analysis_run.get("region_sales_json", []),
                "forecast": analysis_run.get("forecast_json", []),
                "rfm": analysis_run.get("rfm_json", {}),
                "what_if": (analysis_run.get("rfm_json", {}) and {}) or {},
            }
            computed = _compute_analysis_bundle(FiltersPayload(**analysis_run.get("filters_json", {})))
            evidence["what_if"] = computed.get("what_if", {})

            try:
                raw_sample = get_raw_data_sample(dataset_id, limit=50)
                data_stats = get_data_statistics(dataset_id)
                if raw_sample:
                    evidence["raw_data_sample"] = raw_sample[:20]
                if data_stats:
                    evidence["data_statistics"] = data_stats
            except Exception as e:
                logger.warning(f"Could not load raw data for insights: {e}")

            try:
                knowledge_docs = get_all_knowledge_for_dataset(dataset_id, limit=10)
                if knowledge_docs:
                    evidence["knowledge_documents"] = knowledge_docs
            except Exception as e:
                logger.warning(f"Could not load knowledge documents: {e}")

            # widgets = _default_widgets(evidence)
            # summary = "AI insights được tạo từ KPI, forecast và RFM hiện tại."
            # suggested_prompts = [
            #     "Rủi ro lớn nhất trong 30 ngày tới là gì?",
            #     "Nên ưu tiên category nào để cải thiện lợi nhuận",
            #     "Đánh giá hiệu suất kinh doanh hiện tại",
            #     "So sánh doanh thu giữa các region",
            # ]

            # client = _get_openai_client()
            # model_name = os.getenv("OPENROUTER_MODEL") or os.getenv("OPENAI_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
            # if client is not None:
            #     system_prompt = (
            #         "Bạn là trợ lý phân tích dữ liệu kinh doanh (BI Analyst). "
            #         "Nhiệm vụ: phân tích dữ liệu và đưa ra đánh giá cụ thể, có số liệu.\n\n"
            #         "QUY TẮC BẮT BUỘC:\n"
            #         "1. CHỈ sử dụng dữ liệu được cung cấp trong evidence — KHÔNG bịa số.\n"
            #         "2. Trả lời NGẮN GỌN, TẬP TRUNG vào nội dung chính — không vòng vo.\n"
            #         "3. ĐƯA RA ĐÁNH GIÁ cụ thể (tốt/xấu/cần cải thiện) kèm lý do.\n"
            #         "4. Dùng tiếng Việt.\n"
            #         "5. Return strictly valid JSON with keys: executive_summary_markdown, widgets, suggested_prompts."
            #     )
            #     user_prompt = (
            #         "Evidence JSON:\n"
            #         f"{json.dumps(_coerce_for_json(evidence), ensure_ascii=False)}\n\n"
            #         "Rules:\n"
            #         "- Return 3 to 6 widgets.\n"
            #         "- Include at least one insight, one risk, one what_if.\n"
            #         "- content_markdown uses bullet lines starting with '- '.\n"
            #         "- Đưa ra ĐÁNH GIÁ cụ thể cho mỗi widget, không chỉ liệt kê số.\n"
            #         "- suggested_prompts phải bằng tiếng Việt, cụ thể và liên quan đến dữ liệu.\n"
            #         "Return JSON only."
            #     )
            #     try:
            #         response = client.chat.completions.create(
            #             model=model_name,
            #             temperature=0.2,
            #             messages=[
            #                 {"role": "system", "content": system_prompt},
            #                 {"role": "user", "content": user_prompt},
            #             ],
            #             response_format={"type": "json_object"},
            #         )
            #         parsed = json.loads(response.choices[0].message.content)
            #         widgets = parsed.get("widgets", widgets) or widgets
            #         summary = parsed.get("executive_summary_markdown", summary)
            #         suggested_prompts = parsed.get("suggested_prompts", suggested_prompts)
            #     except Exception as llm_error:
            #         logger.warning("OpenAI insights fallback used: %s", llm_error)
            
            widgets = _default_widgets(evidence)
            summary = "AI insights được tạo từ KPI, forecast và RFM hiện tại."
            suggested_prompts = [
                "Rủi ro lớn nhất trong 30 ngày tới là gì?",
                "Nên ưu tiên category nào để cải thiện lợi nhuận",
                "Đánh giá hiệu suất kinh doanh hiện tại",
                "So sánh doanh thu giữa các region",
            ]

            # === TẠM TẮT LLM ĐỂ DÙNG FORMAT LOCAL ===
            client = None   # ← Tắt LLM để insight hiển thị đúng format mới

            # Nếu bạn muốn bật LLM sau này, hãy comment dòng trên và chỉnh system_prompt
            # client = _get_openai_client()
            # model_name = os.getenv("OPENROUTER_MODEL") or os.getenv("OPENAI_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
            # if client is not None:
            #     ... (giữ nguyên phần LLM cũ hoặc chỉnh sau)

            save_widgets(req.analysis_run_id, _coerce_for_json(widgets))
            return {
                "analysis_run_id": req.analysis_run_id,
                "executive_summary_markdown": summary,
                "widgets": _coerce_for_json(widgets),
                "suggested_prompts": suggested_prompts,
            }

        # Chart-level insight request (chartId present)
        if payload.get("chartId"):
            # Create a temporary analysis run and save widgets so they are persisted
            filters = payload.get("filters", {}) or {}
            dataset_id = get_active_dataset_id()
            computed = _compute_analysis_bundle(FiltersPayload(**filters)) if isinstance(filters, dict) else _compute_analysis_bundle(FiltersPayload())
            analysis_run_id = save_analysis_run(dataset_id or get_active_dataset_id(), filters, computed)
            evidence = {
                "kpis": computed.get("kpis", {}),
                "sales_trend": computed.get("sales_trend", []),
                "category_sales": computed.get("category_sales", []),
                "region_sales": computed.get("region_sales", []),
                "forecast": computed.get("forecast", []),
                "rfm": computed.get("rfm", {}),
                "what_if": computed.get("what_if", {}),
            }
            widgets = _default_widgets(evidence)
            save_widgets(analysis_run_id, _coerce_for_json(widgets))
            # Retrieve saved widget IDs from DB
            try:
                saved = get_latest_widgets(analysis_run_id)
                first = saved[0] if saved else (widgets[0] if widgets else {})
                widget_id = first.get("id")
            except Exception:
                first = widgets[0] if widgets else {}
                widget_id = first.get("id") or None
            # Return a ChartInsightResponse-like object
            response = {
                "id": widget_id or str(uuid.uuid4()),
                "summary": first.get("content_markdown", ""),
                "highlights": [],
                "explanations": [],
                "actions": [],
                "confidence": 0.7,
                "model_meta": {"model_name": "local-bundle", "latency_ms": 10},
                "cached": False,
                "status": "succeeded",
            }
            return response

        raise HTTPException(status_code=400, detail="Unsupported payload for /api/ai/insights")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in generate_ai_insights: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/insights/{insight_id}")
@limiter.limit("60/minute")
def get_chart_insight(request: Request, insight_id: str, current_user: dict = Depends(get_current_user)):
    try:
        widget = None
        try:
            widget = get_widget_by_id(insight_id)
        except Exception:
            widget = None

        if not widget:
            raise HTTPException(status_code=404, detail="Insight not found")

        summary = widget.get("content_markdown", "")
        return {
            "id": widget.get("id"),
            "summary": summary,
            "highlights": [],
            "explanations": [],
            "actions": [],
            "confidence": 0.75,
            "model_meta": {"model_name": "persisted", "latency_ms": 5},
            "cached": True,
            "status": "succeeded",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching insight %s: %s", insight_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ai/insights/{insight_id}/feedback")
def post_chart_insight_feedback(insight_id: str, payload: dict, current_user: dict = Depends(get_current_user)):
    # For now we acknowledge feedback; can be stored later.
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
