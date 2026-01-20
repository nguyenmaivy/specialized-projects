from fastapi.testclient import TestClient
from unittest.mock import patch
import pandas as pd
from backend.main import app

client = TestClient(app)

# Mock data for testing
mock_df_data = {
    "Order Date": pd.to_datetime(["2023-01-01", "2023-01-02"]),
    "Category": ["Furniture", "Technology"],
    "Region": ["North", "South"],
    "Sales": [100, 200],
    "Profit": [10, 20],
    "Order ID": ["ORD1", "ORD2"],
    "Discount": [0.1, 0.2]
}
mock_df = pd.DataFrame(mock_df_data)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to AI Sales Forecasting API"
    }


@patch("backend.main.load_data")
def test_get_filters(mock_load_data):
    mock_load_data.return_value = mock_df
    response = client.get("/api/filters")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "regions" in data
    assert "Furniture" in data["categories"]
    assert "North" in data["regions"]


@patch("backend.main.load_data")
def test_get_kpis(mock_load_data):
    mock_load_data.return_value = mock_df
    response = client.get("/api/kpis")
    assert response.status_code == 200
    data = response.json()
    assert data["total_sales"] == 300
    assert data["total_profit"] == 30
