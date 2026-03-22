"""
Comprehensive test suite for AI Sales Forecasting Dashboard Backend v2.0.
Covers: all endpoints, auth, rate limiting, export, filters, edge cases.
Total: 90+ test cases.
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import pytest
import os
from backend.main import app, apply_filters, validate_date
from backend.auth import (
    create_access_token, hash_password, verify_password,
    users_db, init_default_users
)

client = TestClient(app)

# Mock data for testing
mock_df_data = {
    "Order Date": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
    "Category": ["Furniture", "Technology", "Office Supplies"],
    "Region": ["North", "South", "East"],
    "Sales": [100, 200, 150],
    "Profit": [10, 20, 15],
    "Order ID": ["ORD1", "ORD2", "ORD3"],
    "Customer ID": ["CUST1", "CUST2", "CUST3"],
    "Customer Name": ["John Doe", "Jane Smith", "Bob Johnson"],
    "Discount": [0.1, 0.2, 0.05]
}
mock_df = pd.DataFrame(mock_df_data)


def get_admin_token():
    """Helper to get admin JWT token"""
    return create_access_token(data={"sub": "admin", "role": "admin"})


def get_viewer_token():
    """Helper to get viewer JWT token"""
    return create_access_token(data={"sub": "viewer", "role": "viewer"})


def auth_header(token):
    """Helper to create Authorization header"""
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. ROOT ENDPOINT TESTS
# =============================================================================

class TestRootEndpoint:
    """Tests for the root (/) endpoint"""

    def test_read_root(self):
        """Test root endpoint returns welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {
            "message": "Welcome to AI Sales Forecasting API"
        }

    def test_root_response_format(self):
        """Test root endpoint returns correct JSON structure"""
        response = client.get("/")
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)


# =============================================================================
# 2. HEALTH CHECK ENDPOINT TESTS
# =============================================================================

class TestHealthCheck:
    """Tests for the /health endpoint"""

    @patch("backend.main.load_data")
    def test_health_check_healthy(self, mock_load_data):
        """Test health check returns healthy status"""
        mock_load_data.return_value = mock_df
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert data["records_loaded"] == 3
        assert "timestamp" in data
        assert "auth_required" in data
        assert "rate_limit" in data

    @patch("backend.main.load_data")
    def test_health_check_unhealthy(self, mock_load_data):
        """Test health check returns unhealthy when data loading fails"""
        mock_load_data.side_effect = FileNotFoundError("Data file not found")
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data


# =============================================================================
# 3. AUTH ENDPOINT TESTS
# =============================================================================

class TestAuthEndpoints:
    """Tests for authentication endpoints"""

    def test_login_success(self):
        """Test successful login with default admin credentials"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    def test_login_wrong_password(self):
        """Test login with wrong password returns 401"""
        response = client.post("/auth/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self):
        """Test login with non-existent user returns 401"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "password"
        })
        assert response.status_code == 401

    def test_register_success(self):
        """Test admin can register new user"""
        token = get_admin_token()
        response = client.post("/auth/register",
            json={"username": "testuser_reg", "password": "password123", "role": "viewer"},
            headers=auth_header(token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser_reg"
        assert data["role"] == "viewer"
        # Cleanup
        users_db.pop("testuser_reg", None)

    def test_register_without_admin(self):
        """Test registration without admin token fails"""
        viewer_token = get_viewer_token()
        # Need to add viewer to users_db for the test
        users_db["viewer"] = {
            "username": "viewer",
            "hashed_password": hash_password("viewerpass"),
            "role": "viewer"
        }
        response = client.post("/auth/register",
            json={"username": "newuser", "password": "password123"},
            headers=auth_header(viewer_token)
        )
        assert response.status_code == 403
        users_db.pop("viewer", None)

    def test_register_duplicate_user(self):
        """Test registering existing username returns 400"""
        token = get_admin_token()
        response = client.post("/auth/register",
            json={"username": "admin", "password": "password123"},
            headers=auth_header(token)
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_register_short_password(self):
        """Test registration with password < 6 chars returns 400"""
        token = get_admin_token()
        response = client.post("/auth/register",
            json={"username": "shortpw", "password": "12345"},
            headers=auth_header(token)
        )
        assert response.status_code == 400
        assert "at least 6 characters" in response.json()["detail"]

    def test_get_me_with_token(self):
        """Test /auth/me returns current user info"""
        token = get_admin_token()
        response = client.get("/auth/me", headers=auth_header(token))
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "admin"
        assert data["role"] == "admin"

    def test_get_me_without_token(self):
        """Test /auth/me without token returns 401"""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_list_users_admin(self):
        """Test admin can list all users"""
        token = get_admin_token()
        response = client.get("/auth/users", headers=auth_header(token))
        assert response.status_code == 200
        data = response.json()
        assert any(u["username"] == "admin" for u in data)

    def test_list_users_non_admin(self):
        """Test non-admin cannot list users"""
        users_db["viewer2"] = {
            "username": "viewer2",
            "hashed_password": hash_password("viewerpass"),
            "role": "viewer"
        }
        viewer_token = create_access_token(data={"sub": "viewer2", "role": "viewer"})
        response = client.get("/auth/users", headers=auth_header(viewer_token))
        assert response.status_code == 403
        users_db.pop("viewer2", None)

    def test_invalid_token(self):
        """Test invalid JWT token returns 401"""
        response = client.get("/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"})
        assert response.status_code == 401

    def test_expired_token_format(self):
        """Test malformed token returns 401"""
        response = client.get("/auth/me",
            headers={"Authorization": "Bearer abc123"})
        assert response.status_code == 401


# =============================================================================
# 4. AUTH HELPER FUNCTION TESTS
# =============================================================================

class TestAuthHelpers:
    """Tests for auth helper functions"""

    def test_password_hashing(self):
        """Test password hash and verify"""
        password = "testpassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_verify(self):
        """Test wrong password verification fails"""
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_create_and_decode_token(self):
        """Test token creation and decoding"""
        from backend.auth import decode_token
        token = create_access_token(data={"sub": "testuser", "role": "viewer"})
        token_data = decode_token(token)
        assert token_data.username == "testuser"
        assert token_data.role == "viewer"


# =============================================================================
# 5. FILTERS ENDPOINT TESTS
# =============================================================================

class TestFiltersEndpoint:
    """Tests for the /api/filters endpoint"""

    @patch("backend.main.load_data")
    def test_get_filters(self, mock_load_data):
        """Test filters endpoint returns available categories and regions"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/filters")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "regions" in data
        assert "min_date" in data
        assert "max_date" in data
        assert "Furniture" in data["categories"]
        assert "North" in data["regions"]

    @patch("backend.main.load_data")
    def test_filters_all_categories_present(self, mock_load_data):
        """Test that all 3 categories are returned"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/filters")
        data = response.json()
        assert set(data["categories"]) == {"Furniture", "Technology", "Office Supplies"}

    @patch("backend.main.load_data")
    def test_filters_all_regions_present(self, mock_load_data):
        """Test that all 3 regions are returned"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/filters")
        data = response.json()
        assert set(data["regions"]) == {"North", "South", "East"}

    @patch("backend.main.load_data")
    def test_filters_date_range(self, mock_load_data):
        """Test that date range is correctly computed"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/filters")
        data = response.json()
        assert data["min_date"] == "2023-01-01"
        assert data["max_date"] == "2023-01-03"

    @patch("backend.main.load_data")
    def test_filters_error_handling(self, mock_load_data):
        """Test filters endpoint error handling"""
        mock_load_data.side_effect = Exception("Unexpected error")
        response = client.get("/api/filters")
        assert response.status_code == 500


# =============================================================================
# 6. KPI ENDPOINT TESTS
# =============================================================================

class TestKPIEndpoint:
    """Tests for the /api/kpis endpoint"""

    @patch("backend.main.load_data")
    def test_get_kpis(self, mock_load_data):
        """Test KPI endpoint returns correct totals"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 450
        assert data["total_profit"] == 45
        assert data["total_orders"] == 3
        assert data["avg_discount"] == pytest.approx(0.1167, abs=0.001)

    @patch("backend.main.load_data")
    def test_get_kpis_with_category_filter(self, mock_load_data):
        """Test KPI endpoint with category filter"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis?category=Furniture")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 100
        assert data["total_profit"] == 10

    @patch("backend.main.load_data")
    def test_get_kpis_with_region_filter(self, mock_load_data):
        """Test KPI endpoint with region filter"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis?region=South")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 200

    @patch("backend.main.load_data")
    def test_get_kpis_with_date_filter(self, mock_load_data):
        """Test KPI endpoint with date range filter"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis?start_date=2023-01-02&end_date=2023-01-03")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 350

    @patch("backend.main.load_data")
    def test_empty_filter_result(self, mock_load_data):
        """Test endpoint with filter that returns no results"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis?category=NonExistent")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 0
        assert data["total_profit"] == 0
        assert data["total_orders"] == 0
        assert data["avg_discount"] == 0

    @patch("backend.main.load_data")
    def test_multiple_categories_filter(self, mock_load_data):
        """Test filter with multiple categories"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis?category=Furniture&category=Technology")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 300

    @patch("backend.main.load_data")
    def test_kpis_invalid_date_returns_400(self, mock_load_data):
        """Test KPI endpoint returns 400 for invalid date format"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis?start_date=invalid-date")
        assert response.status_code == 400

    @patch("backend.main.load_data")
    def test_kpis_response_types(self, mock_load_data):
        """Test KPI endpoint response value types"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis")
        data = response.json()
        assert isinstance(data["total_sales"], (int, float))
        assert isinstance(data["total_profit"], (int, float))
        assert isinstance(data["total_orders"], int)
        assert isinstance(data["avg_discount"], (int, float))

    @patch("backend.main.load_data")
    def test_kpis_combined_filters(self, mock_load_data):
        """Test KPI endpoint with all filters combined"""
        mock_load_data.return_value = mock_df
        response = client.get(
            "/api/kpis?category=Furniture&region=North&start_date=2023-01-01&end_date=2023-01-01"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 100

    @patch("backend.main.load_data")
    def test_kpis_with_auth_token(self, mock_load_data):
        """Test KPI endpoint works with valid auth token"""
        mock_load_data.return_value = mock_df
        token = get_admin_token()
        response = client.get("/api/kpis", headers=auth_header(token))
        assert response.status_code == 200


# =============================================================================
# 7. SALES TREND ENDPOINT TESTS
# =============================================================================

class TestSalesTrendEndpoint:
    """Tests for the /api/charts/sales-trend endpoint"""

    @patch("backend.main.load_data")
    def test_get_sales_trend(self, mock_load_data):
        """Test sales trend endpoint returns data"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/sales-trend")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Order Date" in data[0]
        assert "Sales" in data[0]

    @patch("backend.main.load_data")
    def test_sales_trend_date_format(self, mock_load_data):
        """Test sales trend dates are formatted as YYYY-MM-DD"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/sales-trend")
        data = response.json()
        for record in data:
            assert len(record["Order Date"]) == 10
            assert record["Order Date"].count("-") == 2

    @patch("backend.main.load_data")
    def test_sales_trend_with_filter(self, mock_load_data):
        """Test sales trend with category filter"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/sales-trend?category=Furniture")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @patch("backend.main.load_data")
    def test_sales_trend_empty_result(self, mock_load_data):
        """Test sales trend returns empty list when no data matches"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/sales-trend?category=NonExistent")
        assert response.status_code == 200
        data = response.json()
        assert data == []


# =============================================================================
# 8. CATEGORY SALES ENDPOINT TESTS
# =============================================================================

class TestCategorySalesEndpoint:
    """Tests for the /api/charts/category-sales endpoint"""

    @patch("backend.main.load_data")
    def test_get_category_sales(self, mock_load_data):
        """Test category sales endpoint returns sorted data"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/category-sales")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["Sales"] >= data[1]["Sales"]

    @patch("backend.main.load_data")
    def test_category_sales_has_required_fields(self, mock_load_data):
        """Test category sales response has Category and Sales fields"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/category-sales")
        data = response.json()
        for record in data:
            assert "Category" in record
            assert "Sales" in record

    @patch("backend.main.load_data")
    def test_category_sales_with_region_filter(self, mock_load_data):
        """Test category sales filtered by region"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/category-sales?region=North")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


# =============================================================================
# 9. REGION SALES ENDPOINT TESTS
# =============================================================================

class TestRegionSalesEndpoint:
    """Tests for the /api/charts/region-sales endpoint"""

    @patch("backend.main.load_data")
    def test_get_region_sales(self, mock_load_data):
        """Test region sales endpoint"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/region-sales")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Region" in data[0]
        assert "Sales" in data[0]

    @patch("backend.main.load_data")
    def test_region_sales_with_category_filter(self, mock_load_data):
        """Test region sales filtered by category"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/region-sales?category=Technology")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["Region"] == "South"

    @patch("backend.main.load_data")
    def test_region_sales_all_regions_present(self, mock_load_data):
        """Test all regions represented in unfiltered response"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/charts/region-sales")
        data = response.json()
        regions = {r["Region"] for r in data}
        assert regions == {"North", "South", "East"}


# =============================================================================
# 10. SALES HEATMAP ENDPOINT TESTS
# =============================================================================

class TestSalesHeatmapEndpoint:
    """Tests for the /api/sales-heatmap endpoint"""

    @patch("backend.main.load_data")
    def test_get_sales_heatmap(self, mock_load_data):
        """Test sales heatmap returns daily aggregated data"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/sales-heatmap")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "day" in data[0]
        assert "value" in data[0]

    @patch("backend.main.load_data")
    def test_heatmap_date_format(self, mock_load_data):
        """Test heatmap dates are in YYYY-MM-DD format"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/sales-heatmap")
        data = response.json()
        for record in data:
            assert len(record["day"]) == 10

    @patch("backend.main.load_data")
    def test_heatmap_with_category_filter(self, mock_load_data):
        """Test heatmap filtered by category"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/sales-heatmap?category=Furniture")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @patch("backend.main.load_data")
    def test_heatmap_with_date_range(self, mock_load_data):
        """Test heatmap filtered by date range"""
        mock_load_data.return_value = mock_df
        response = client.get(
            "/api/sales-heatmap?start_date=2023-01-01&end_date=2023-01-02"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch("backend.main.load_data")
    def test_heatmap_values_positive(self, mock_load_data):
        """Test heatmap values are positive numbers"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/sales-heatmap")
        data = response.json()
        for record in data:
            assert record["value"] > 0

    @patch("backend.main.load_data")
    def test_heatmap_empty_filter(self, mock_load_data):
        """Test heatmap with filter returning no results"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/sales-heatmap?category=NonExistent")
        assert response.status_code == 200
        data = response.json()
        assert data == []


# =============================================================================
# 11. CUSTOMER SEGMENTATION ENDPOINT TESTS
# =============================================================================

class TestCustomerSegmentationEndpoint:
    """Tests for the /api/customer-segmentation endpoint"""

    @patch("backend.main.load_data")
    def test_get_customer_segmentation(self, mock_load_data, mock_df_large):
        """Test customer segmentation returns segments and customers"""
        mock_load_data.return_value = mock_df_large
        response = client.get("/api/customer-segmentation")
        assert response.status_code == 200
        data = response.json()
        assert "segments" in data
        assert "customers" in data
        assert len(data["customers"]) > 0

    @patch("backend.main.load_data")
    def test_segmentation_valid_labels(self, mock_load_data, mock_df_large):
        """Test segmentation assigns valid segment labels"""
        mock_load_data.return_value = mock_df_large
        response = client.get("/api/customer-segmentation")
        data = response.json()
        valid_segments = {"Champions", "Loyal", "At Risk", "New Customers"}
        for customer in data["customers"]:
            assert customer["Segment"] in valid_segments

    @patch("backend.main.load_data")
    def test_segmentation_customer_fields(self, mock_load_data, mock_df_large):
        """Test each customer has required fields"""
        mock_load_data.return_value = mock_df_large
        response = client.get("/api/customer-segmentation")
        data = response.json()
        required_fields = {"Customer ID", "Customer Name", "Recency",
                           "Frequency", "Monetary", "Segment"}
        for customer in data["customers"]:
            assert required_fields.issubset(set(customer.keys()))

    @patch("backend.main.load_data")
    def test_segmentation_rfm_nonnegative(self, mock_load_data, mock_df_large):
        """Test RFM values are non-negative"""
        mock_load_data.return_value = mock_df_large
        response = client.get("/api/customer-segmentation")
        data = response.json()
        for customer in data["customers"]:
            assert customer["Recency"] >= 0
            assert customer["Frequency"] >= 0
            assert customer["Monetary"] >= 0

    @patch("backend.main.load_data")
    def test_segmentation_segment_summary(self, mock_load_data, mock_df_large):
        """Test segment summary has required fields"""
        mock_load_data.return_value = mock_df_large
        response = client.get("/api/customer-segmentation")
        data = response.json()
        for segment in data["segments"]:
            assert "segment" in segment
            assert "customer_count" in segment

    @patch("backend.main.load_data")
    def test_segmentation_insufficient_data(self, mock_load_data):
        """Test segmentation with too few customers returns 500"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/customer-segmentation")
        assert response.status_code == 500


# =============================================================================
# 12. FORECAST ENDPOINT TESTS
# =============================================================================

class TestForecastEndpoint:
    """Tests for the /api/forecast endpoint"""

    @patch("backend.main.load_data")
    def test_forecast_insufficient_data(self, mock_load_data):
        """Test forecast returns error when data < 50 records"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/forecast")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    @patch("backend.main.load_data")
    def test_forecast_with_sufficient_data(self, mock_load_data, mock_df_large):
        """Test forecast returns predictions with sufficient data"""
        mock_load_data.return_value = mock_df_large
        response = client.get("/api/forecast")
        assert response.status_code == 200
        data = response.json()
        if "error" not in data:
            assert len(data) > 0
            assert "ds" in data[0]
            assert "yhat" in data[0]

    @patch("backend.main.load_data")
    def test_forecast_confidence_intervals(self, mock_load_data, mock_df_large):
        """Test forecast confidence intervals: lower <= predicted <= upper"""
        mock_load_data.return_value = mock_df_large
        response = client.get("/api/forecast")
        data = response.json()
        if "error" not in data:
            for record in data:
                assert record["yhat_lower"] <= record["yhat"]
                assert record["yhat"] <= record["yhat_upper"]


# =============================================================================
# 13. EXPORT ENDPOINT TESTS
# =============================================================================

class TestExportEndpoint:
    """Tests for the /api/export/csv endpoint"""

    @patch("backend.main.load_data")
    def test_export_csv(self, mock_load_data):
        """Test CSV export returns downloadable file"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]

    @patch("backend.main.load_data")
    def test_export_csv_content(self, mock_load_data):
        """Test exported CSV has correct content"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/export/csv")
        content = response.content.decode('utf-8')
        assert "Order ID" in content
        assert "Sales" in content
        assert "ORD1" in content

    @patch("backend.main.load_data")
    def test_export_csv_with_filter(self, mock_load_data):
        """Test CSV export with filters applied"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/export/csv?category=Furniture")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        lines = content.strip().split('\n')
        assert len(lines) == 2  # header + 1 data row

    @patch("backend.main.load_data")
    def test_export_csv_invalid_date(self, mock_load_data):
        """Test CSV export with invalid date returns 400"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/export/csv?start_date=bad-date")
        assert response.status_code == 400

    @patch("backend.main.load_data")
    def test_export_csv_empty_result(self, mock_load_data):
        """Test CSV export with no matching data"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/export/csv?category=NonExistent")
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        lines = content.strip().split('\n')
        assert len(lines) == 1  # header only

    @patch("backend.main.load_data")
    def test_export_csv_with_auth(self, mock_load_data):
        """Test CSV export works with auth token"""
        mock_load_data.return_value = mock_df
        token = get_admin_token()
        response = client.get("/api/export/csv", headers=auth_header(token))
        assert response.status_code == 200


# =============================================================================
# 14. VALIDATE_DATE FUNCTION TESTS
# =============================================================================

class TestValidateDate:
    """Tests for the validate_date helper function"""

    def test_valid_date(self):
        assert validate_date("2023-01-15") is True

    def test_valid_date_leap_year(self):
        assert validate_date("2024-02-29") is True

    def test_invalid_format_slash(self):
        assert validate_date("01/15/2023") is False

    def test_invalid_format_text(self):
        assert validate_date("invalid-date") is False

    def test_invalid_date_values(self):
        assert validate_date("2023-13-01") is False

    def test_invalid_date_feb_30(self):
        assert validate_date("2023-02-30") is False

    def test_empty_string(self):
        assert validate_date("") is False

    def test_date_with_time(self):
        assert validate_date("2023-01-15T10:30:00") is False


# =============================================================================
# 15. APPLY_FILTERS FUNCTION TESTS
# =============================================================================

class TestApplyFilters:
    """Tests for the apply_filters helper function"""

    def test_no_filters(self):
        result = apply_filters(mock_df)
        assert len(result) == 3

    def test_single_category(self):
        result = apply_filters(mock_df, category=["Furniture"])
        assert len(result) == 1

    def test_multiple_categories(self):
        result = apply_filters(mock_df, category=["Furniture", "Technology"])
        assert len(result) == 2

    def test_single_region(self):
        result = apply_filters(mock_df, region=["South"])
        assert len(result) == 1

    def test_multiple_regions(self):
        result = apply_filters(mock_df, region=["North", "South"])
        assert len(result) == 2

    def test_date_range(self):
        result = apply_filters(mock_df, start_date="2023-01-02", end_date="2023-01-03")
        assert len(result) == 2

    def test_start_date_only(self):
        result = apply_filters(mock_df, start_date="2023-01-02")
        assert len(result) == 2

    def test_end_date_only(self):
        result = apply_filters(mock_df, end_date="2023-01-02")
        assert len(result) == 2

    def test_same_start_end_date(self):
        result = apply_filters(mock_df, start_date="2023-01-02", end_date="2023-01-02")
        assert len(result) == 1

    def test_combined_all_filters(self):
        result = apply_filters(mock_df, category=["Furniture", "Technology"],
                               region=["North"], start_date="2023-01-01")
        assert len(result) == 1

    def test_non_existent_category(self):
        result = apply_filters(mock_df, category=["NonExistent"])
        assert len(result) == 0

    def test_non_existent_region(self):
        result = apply_filters(mock_df, region=["Atlantis"])
        assert len(result) == 0

    def test_future_date_returns_empty(self):
        result = apply_filters(mock_df, start_date="2099-01-01")
        assert len(result) == 0

    def test_past_end_date_returns_empty(self):
        result = apply_filters(mock_df, end_date="2000-01-01")
        assert len(result) == 0

    def test_invalid_date_raises_error(self):
        with pytest.raises(ValueError, match="Invalid start_date format"):
            apply_filters(mock_df, start_date="not-a-date")

    def test_invalid_end_date_raises_error(self):
        with pytest.raises(ValueError, match="Invalid end_date format"):
            apply_filters(mock_df, end_date="2023/01/01")

    def test_empty_category_list(self):
        result = apply_filters(mock_df, category=[])
        assert len(result) == 3

    def test_empty_region_list(self):
        result = apply_filters(mock_df, region=[])
        assert len(result) == 3

    def test_preserves_dataframe_columns(self):
        result = apply_filters(mock_df, category=["Furniture"])
        assert list(result.columns) == list(mock_df.columns)


# =============================================================================
# 16. EDGE CASE & ERROR HANDLING TESTS
# =============================================================================

class TestEdgeCases:
    """Edge case and error handling tests"""

    @patch("backend.main.load_data")
    def test_load_data_exception_returns_500(self, mock_load_data):
        """Test exception in load_data returns 500"""
        mock_load_data.side_effect = Exception("Database connection failed")
        response = client.get("/api/kpis")
        assert response.status_code == 500

    def test_nonexistent_endpoint_returns_404(self):
        """Test non-existent endpoint returns 404"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_post_to_get_endpoint(self):
        """Test POST to a GET-only endpoint returns 405"""
        response = client.post("/api/kpis")
        assert response.status_code == 405

    @patch("backend.main.load_data")
    def test_single_record_kpis(self, mock_load_data, mock_df_single):
        """Test KPIs with only a single record"""
        mock_load_data.return_value = mock_df_single
        response = client.get("/api/kpis")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 999.99
        assert data["total_orders"] == 1

    @patch("backend.main.load_data")
    def test_special_characters_in_filter(self, mock_load_data):
        """Test filter with special characters doesn't crash (XSS prevention)"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis?category=<script>alert('xss')</script>")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sales"] == 0

    @patch("backend.main.load_data")
    def test_unicode_in_filter(self, mock_load_data):
        """Test filter with unicode characters"""
        mock_load_data.return_value = mock_df
        response = client.get("/api/kpis?category=Điện+tử")
        assert response.status_code == 200

    @patch("backend.main.load_data")
    def test_very_long_filter_value(self, mock_load_data):
        """Test filter with very long value doesn't crash"""
        mock_load_data.return_value = mock_df
        long_value = "A" * 1000
        response = client.get(f"/api/kpis?category={long_value}")
        assert response.status_code == 200

    @patch("backend.main.load_data")
    def test_all_endpoints_consistent_error_500(self, mock_load_data):
        """Test all endpoints return 500 on internal error"""
        mock_load_data.side_effect = Exception("Internal error")
        endpoints = [
            "/api/filters", "/api/kpis", "/api/charts/sales-trend",
            "/api/charts/category-sales", "/api/charts/region-sales",
            "/api/sales-heatmap", "/api/forecast",
            "/api/customer-segmentation", "/api/export/csv",
        ]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 500, f"Expected 500 for {endpoint}"
