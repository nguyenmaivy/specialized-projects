# Machine Learning - Prophet & K-Means

## Tổng quan

Dự án sử dụng 2 thuật toán Machine Learning chính:
1. **Facebook Prophet** - Time series forecasting (Dự đoán doanh số)
2. **K-Means Clustering** - Customer segmentation (Phân khúc khách hàng)

---

## 📚 Kiến thức nền tảng

### 1. Statistics Basics
**Thời gian học**: 1 tuần

#### Concepts cần biết:
- **Mean (Trung bình)**: Tổng / Số lượng
- **Median (Trung vị)**: Giá trị ở giữa khi sắp xếp
- **Standard Deviation (Độ lệch chuẩn)**: Đo mức độ phân tán
- **Correlation (Tương quan)**: Mối quan hệ giữa 2 biến
- **Distribution (Phân phối)**: Normal distribution, skewness

#### Tài liệu học:
- [Khan Academy - Statistics](https://www.khanacademy.org/math/statistics-probability)
- [StatQuest YouTube Channel](https://www.youtube.com/c/joshstarmer)

---

## 🔮 Part 1: Facebook Prophet - Sales Forecasting

### Giới thiệu
Prophet là thư viện của Facebook để dự đoán time series data (dữ liệu theo thời gian). Nó tự động xử lý:
- **Trend**: Xu hướng tăng/giảm theo thời gian
- **Seasonality**: Tính chu kỳ (theo tuần, tháng, năm)
- **Holidays**: Ngày lễ ảnh hưởng đến doanh số

### Cách hoạt động

Prophet sử dụng công thức:
```
y(t) = g(t) + s(t) + h(t) + ε
```
- `g(t)`: Growth (Xu hướng)
- `s(t)`: Seasonality (Tính mùa vụ)
- `h(t)`: Holidays (Ngày lễ)
- `ε`: Error (Sai số)

### Data Format
Prophet yêu cầu DataFrame với 2 cột:
- `ds`: Date (datetime)
- `y`: Value to predict (số cần dự đoán)

### Code Implementation

```python
from prophet import Prophet
import pandas as pd

# 1. Prepare data
df = pd.read_csv('sales.csv')
sales_df = df[["Order Date", "Sales"]].rename(
    columns={"Order Date": "ds", "Sales": "y"}
)

# Group by date (aggregate multiple orders per day)
sales_df = sales_df.groupby("ds").sum().reset_index()

# 2. Train model
model = Prophet()
model.fit(sales_df)

# 3. Create future dates
future = model.make_future_dataframe(periods=30)  # 30 days ahead

# 4. Make predictions
forecast = model.predict(future)

# 5. Get results
forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(30)
```

### Output Columns
- `yhat`: Predicted value (dự đoán)
- `yhat_lower`: Lower bound (giới hạn dưới - 95% confidence)
- `yhat_upper`: Upper bound (giới hạn trên - 95% confidence)

### Visualization
```python
# Plot forecast
model.plot(forecast)

# Plot components (trend, seasonality)
model.plot_components(forecast)
```

### Hyperparameters (Tùy chỉnh)
```python
model = Prophet(
    yearly_seasonality=True,    # Tính mùa vụ theo năm
    weekly_seasonality=True,    # Tính mùa vụ theo tuần
    daily_seasonality=False,    # Không cần theo ngày
    changepoint_prior_scale=0.05  # Độ nhạy với thay đổi xu hướng
)
```

### Tài liệu học:
- [Prophet Documentation](https://facebook.github.io/prophet/)
- [Prophet Paper](https://peerj.com/preprints/3190/)
- [Time Series Forecasting with Prophet - YouTube](https://www.youtube.com/watch?v=pOYAXv15r3A)

---

## 🎯 Part 2: K-Means Clustering - Customer Segmentation

### Giới thiệu
K-Means là thuật toán **unsupervised learning** (học không giám sát) để nhóm dữ liệu thành K clusters (nhóm).

### RFM Analysis
Trước khi clustering, ta tính **RFM metrics** cho mỗi khách hàng:

- **R**ecency: Số ngày kể từ lần mua cuối
- **F**requency: Số lần mua hàng
- **M**onetary: Tổng tiền đã chi

### Cách hoạt động K-Means

1. **Khởi tạo**: Chọn ngẫu nhiên K centroids (tâm cụm)
2. **Assignment**: Gán mỗi điểm vào cluster gần nhất
3. **Update**: Tính lại centroid của mỗi cluster
4. **Repeat**: Lặp lại bước 2-3 cho đến khi hội tụ

### Code Implementation

```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

# 1. Calculate RFM metrics
reference_date = df["Order Date"].max()

rfm = df.groupby("Customer ID").agg({
    "Order Date": lambda x: (reference_date - x.max()).days,  # Recency
    "Order ID": "count",  # Frequency
    "Sales": "sum"  # Monetary
}).reset_index()

rfm.columns = ["Customer ID", "Recency", "Frequency", "Monetary"]

# 2. Normalize data (quan trọng!)
# K-Means nhạy cảm với scale, phải chuẩn hóa
scaler = StandardScaler()
rfm_normalized = scaler.fit_transform(rfm[["Recency", "Frequency", "Monetary"]])

# 3. Train K-Means
kmeans = KMeans(
    n_clusters=4,      # 4 nhóm khách hàng
    random_state=42,   # Reproducible results
    n_init=10          # Số lần khởi tạo
)
rfm["Cluster"] = kmeans.fit_predict(rfm_normalized)

# 4. Analyze clusters
cluster_stats = rfm.groupby("Cluster").agg({
    "Recency": "mean",
    "Frequency": "mean",
    "Monetary": "mean",
    "Customer ID": "count"
})
print(cluster_stats)
```

### Labeling Clusters
Sau khi có clusters, ta gán nhãn dựa trên đặc điểm:

```python
def assign_segment_label(cluster_id):
    stats = cluster_stats.loc[cluster_id]
    
    # Low Recency + High Frequency + High Monetary = Champions
    if stats["Frequency"] > threshold_freq and stats["Monetary"] > threshold_money:
        return "Champions"
    
    # High Recency = At Risk
    elif stats["Recency"] > threshold_recency:
        return "At Risk"
    
    # Low Frequency + Low Monetary = New Customers
    elif stats["Frequency"] < threshold_freq and stats["Monetary"] < threshold_money:
        return "New Customers"
    
    # Medium values = Loyal
    else:
        return "Loyal"

rfm["Segment"] = rfm["Cluster"].apply(assign_segment_label)
```

### Choosing K (Số clusters)
Dùng **Elbow Method**:

```python
from sklearn.metrics import silhouette_score

inertias = []
silhouette_scores = []

for k in range(2, 11):
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(rfm_normalized)
    inertias.append(kmeans.inertia_)
    silhouette_scores.append(silhouette_score(rfm_normalized, kmeans.labels_))

# Plot elbow curve
import matplotlib.pyplot as plt
plt.plot(range(2, 11), inertias)
plt.xlabel('Number of Clusters')
plt.ylabel('Inertia')
plt.show()
```

### Tài liệu học:
- [Scikit-learn K-Means](https://scikit-learn.org/stable/modules/clustering.html#k-means)
- [StatQuest: K-Means Clustering](https://www.youtube.com/watch?v=4b5d3muPQmA)
- [RFM Analysis Explained](https://www.putler.com/rfm-analysis/)

---

## 🎓 Lộ trình học Machine Learning

### Tuần 1: Statistics Basics
- Mean, median, standard deviation
- Correlation và causation
- Normal distribution

### Tuần 2: Python for ML
- NumPy arrays
- Pandas DataFrames
- Matplotlib visualization

### Tuần 3: Prophet
- Time series concepts
- Train Prophet model
- Interpret forecast results

### Tuần 4: K-Means
- Clustering concepts
- StandardScaler
- Elbow method
- RFM analysis

---

## 🛠 Tools & Libraries

```bash
pip install prophet
pip install scikit-learn
pip install numpy
pip install pandas
pip install matplotlib
```

---

## 📖 Tài liệu tham khảo

### Courses:
- [Andrew Ng - Machine Learning](https://www.coursera.org/learn/machine-learning)
- [Google Machine Learning Crash Course](https://developers.google.com/machine-learning/crash-course)

### Books:
- "Hands-On Machine Learning" - Aurélien Géron
- "Python for Data Analysis" - Wes McKinney

### YouTube Channels:
- StatQuest with Josh Starmer
- 3Blue1Brown (Math visualization)
- sentdex (Python ML tutorials)

---

## 💡 Tips học Machine Learning

1. **Math không cần quá sâu**: Hiểu concept quan trọng hơn công thức
2. **Visualize everything**: Plot data để hiểu pattern
3. **Start simple**: Dùng thư viện có sẵn trước khi code from scratch
4. **Understand the problem**: ML là tool, business problem là mục tiêu
5. **Experiment**: Thử nhiều parameters, so sánh kết quả
6. **Validate results**: Luôn kiểm tra xem model có hợp lý không
