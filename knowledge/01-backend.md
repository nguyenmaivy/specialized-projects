# Backend Development - FastAPI & Python

## Tổng quan

Backend của dự án sử dụng **FastAPI**, một framework Python hiện đại, nhanh và dễ sử dụng để xây dựng RESTful APIs.

---

## 📚 Kiến thức cần học

### 1. Python Fundamentals
**Thời gian học**: 2-3 tuần

#### Nội dung cơ bản:
- **Data Types**: `str`, `int`, `float`, `list`, `dict`, `tuple`, `set`
- **Control Flow**: `if/else`, `for`, `while`, `try/except`
- **Functions**: Định nghĩa, parameters, return values, lambda functions
- **OOP**: Classes, objects, inheritance, methods
- **List Comprehensions**: `[x*2 for x in range(10)]`

#### Tài liệu học:
- [Python Official Tutorial](https://docs.python.org/3/tutorial/)
- [Real Python - Python Basics](https://realpython.com/learning-paths/python-basics/)
- [W3Schools Python](https://www.w3schools.com/python/)

---

### 2. Pandas - Data Manipulation
**Thời gian học**: 1-2 tuần

#### Nội dung:
- **DataFrame**: Cấu trúc dữ liệu chính của Pandas
- **Reading Data**: `pd.read_csv()`, `pd.read_excel()`
- **Data Selection**: `.loc[]`, `.iloc[]`, boolean indexing
- **Filtering**: `df[df['Sales'] > 1000]`
- **Grouping**: `df.groupby('Category').sum()`
- **Aggregation**: `.agg()`, `.sum()`, `.mean()`, `.count()`

#### Code ví dụ trong dự án:
```python
# Load data
df = pd.read_csv('data.csv', encoding='latin-1')

# Filter by date
df = df[df["Order Date"] >= pd.to_datetime(start_date)]

# Group and aggregate
sales_by_category = df.groupby("Category")["Sales"].sum()
```

#### Tài liệu học:
- [Pandas Official Documentation](https://pandas.pydata.org/docs/)
- [Kaggle - Pandas Course](https://www.kaggle.com/learn/pandas)

---

### 3. FastAPI Framework
**Thời gian học**: 1 tuần

#### Nội dung:
- **Routing**: Định nghĩa endpoints với `@app.get()`, `@app.post()`
- **Path Parameters**: `/items/{item_id}`
- **Query Parameters**: `/items?skip=0&limit=10`
- **Request Body**: Nhận JSON data
- **Response Models**: Pydantic models
- **CORS**: Cho phép frontend gọi API

#### Code ví dụ:
```python
from fastapi import FastAPI, Query
from typing import List, Optional

app = FastAPI()

@app.get("/api/kpis")
def get_kpis(
    category: Optional[List[str]] = Query(None),
    region: Optional[List[str]] = Query(None)
):
    # Filter data
    if category:
        df = df[df["Category"].isin(category)]
    
    return {
        "total_sales": float(df["Sales"].sum()),
        "total_profit": float(df["Profit"].sum())
    }
```

#### Tài liệu học:
- [FastAPI Official Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [FastAPI Full Course - YouTube](https://www.youtube.com/watch?v=7t2alSnE2-I)

---

### 4. Facebook Prophet - Time Series Forecasting
**Thời gian học**: 3-5 ngày

#### Nội dung:
- **Time Series Basics**: Trend, seasonality, holidays
- **Prophet Model**: Cách hoạt động
- **Data Format**: Cần 2 cột `ds` (date) và `y` (value)
- **Forecasting**: `model.predict(future)`
- **Visualization**: Plot forecast với confidence intervals

#### Code ví dụ:
```python
from prophet import Prophet

# Prepare data
sales_df = df[["Order Date", "Sales"]].rename(
    columns={"Order Date": "ds", "Sales": "y"}
)
sales_df = sales_df.groupby("ds").sum().reset_index()

# Train model
model = Prophet()
model.fit(sales_df)

# Make forecast
future = model.make_future_dataframe(periods=30)
forecast = model.predict(future)

# Get results
forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
```

#### Tài liệu học:
- [Prophet Official Documentation](https://facebook.github.io/prophet/)
- [Prophet Quick Start](https://facebook.github.io/prophet/docs/quick_start.html)

---

### 5. Scikit-learn - Machine Learning
**Thời gian học**: 1 tuần

#### Nội dung cho dự án:
- **K-Means Clustering**: Phân nhóm khách hàng
- **StandardScaler**: Chuẩn hóa dữ liệu
- **Model Training**: `model.fit()`
- **Prediction**: `model.predict()`

#### Code ví dụ - RFM Clustering:
```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Calculate RFM metrics
rfm = df.groupby("Customer ID").agg({
    "Order Date": lambda x: (max_date - x.max()).days,  # Recency
    "Order ID": "count",  # Frequency
    "Sales": "sum"  # Monetary
})

# Normalize data
scaler = StandardScaler()
rfm_normalized = scaler.fit_transform(rfm)

# K-Means clustering
kmeans = KMeans(n_clusters=4, random_state=42)
rfm["Cluster"] = kmeans.fit_predict(rfm_normalized)
```

#### Tài liệu học:
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [K-Means Clustering Tutorial](https://scikit-learn.org/stable/modules/clustering.html#k-means)

---

## 🎯 Lộ trình học Backend

### Tuần 1-2: Python Basics
- Học syntax cơ bản
- Làm bài tập trên LeetCode/HackerRank
- Thực hành với list, dict, functions

### Tuần 3: Pandas
- Đọc CSV files
- Filter, group, aggregate data
- Làm project nhỏ: Phân tích dữ liệu bán hàng

### Tuần 4: FastAPI
- Tạo API đơn giản
- Thêm query parameters
- Test với Postman/Thunder Client

### Tuần 5: Machine Learning
- Học Prophet cho forecasting
- Học K-Means cho clustering
- Áp dụng vào dữ liệu thật

---

## 🛠 Tools cần cài đặt

1. **Python 3.8+**: [Download](https://www.python.org/downloads/)
2. **VS Code**: [Download](https://code.visualstudio.com/)
3. **Postman**: [Download](https://www.postman.com/) - Test APIs
4. **Git**: [Download](https://git-scm.com/)

### VS Code Extensions:
- Python
- Pylance
- Python Debugger

---

## 📖 Tài liệu tham khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pandas Cheat Sheet](https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf)
- [Prophet Documentation](https://facebook.github.io/prophet/)
- [Scikit-learn Documentation](https://scikit-learn.org/)

---

## 💡 Tips học tập

1. **Thực hành nhiều**: Code mỗi ngày, dù chỉ 30 phút
2. **Đọc code người khác**: GitHub, Stack Overflow
3. **Debug thường xuyên**: Dùng `print()` và debugger
4. **Làm project nhỏ**: Áp dụng ngay những gì học được
5. **Hỏi khi cần**: Stack Overflow, Reddit, Discord communities
