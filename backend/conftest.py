"""
Shared pytest fixtures for AI Sales Forecasting Dashboard tests.
Provides reusable mock data and test client configuration.
"""
import os
# Override AUTH_REQUIRED before importing app so tests always run without auth
os.environ["AUTH_REQUIRED"] = "false"

import sys
from pathlib import Path

# Ensure repo root is on sys.path so `backend.*` imports work even when running pytest from /backend
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture"""
    return TestClient(app)


@pytest.fixture
def mock_df():
    """Basic mock DataFrame with 3 records for simple tests"""
    data = {
        "Order Date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
        "Category": ["Furniture", "Technology", "Office Supplies"],
        "Region": ["North", "South", "East"],
        "Sales": [100.0, 200.0, 150.0],
        "Profit": [10.0, 20.0, 15.0],
        "Order ID": ["ORD1", "ORD2", "ORD3"],
        "Customer ID": ["CUST1", "CUST2", "CUST3"],
        "Customer Name": ["John Doe", "Jane Smith", "Bob Johnson"],
        "Discount": [0.1, 0.2, 0.05]
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_df_large():
    """Large mock DataFrame with 60+ records for forecast testing.
    Prophet requires at least 50 data points.
    """
    np.random.seed(42)
    n = 80
    dates = pd.date_range(start="2022-01-01", periods=n, freq="D")
    categories = np.random.choice(["Furniture", "Technology", "Office Supplies"], n)
    regions = np.random.choice(["North", "South", "East", "West"], n)
    sales = np.random.uniform(50, 500, n).round(2)
    profits = (sales * np.random.uniform(0.05, 0.3, n)).round(2)
    discounts = np.random.uniform(0, 0.4, n).round(2)

    data = {
        "Order Date": dates,
        "Category": categories,
        "Region": regions,
        "Sales": sales,
        "Profit": profits,
        "Order ID": [f"ORD{i}" for i in range(n)],
        "Customer ID": [f"CUST{i % 20}" for i in range(n)],
        "Customer Name": [f"Customer {i % 20}" for i in range(n)],
        "Discount": discounts
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_df_empty():
    """Empty DataFrame with correct columns for edge case testing"""
    return pd.DataFrame({
        "Order Date": pd.Series(dtype="datetime64[ns]"),
        "Category": pd.Series(dtype="str"),
        "Region": pd.Series(dtype="str"),
        "Sales": pd.Series(dtype="float64"),
        "Profit": pd.Series(dtype="float64"),
        "Order ID": pd.Series(dtype="str"),
        "Customer ID": pd.Series(dtype="str"),
        "Customer Name": pd.Series(dtype="str"),
        "Discount": pd.Series(dtype="float64")
    })


@pytest.fixture
def mock_df_single():
    """Single record DataFrame for boundary testing"""
    data = {
        "Order Date": pd.to_datetime(["2023-06-15"]),
        "Category": ["Technology"],
        "Region": ["West"],
        "Sales": [999.99],
        "Profit": [150.0],
        "Order ID": ["ORD-SINGLE"],
        "Customer ID": ["CUST-SINGLE"],
        "Customer Name": ["Single Customer"],
        "Discount": [0.15]
    }
    return pd.DataFrame(data)
