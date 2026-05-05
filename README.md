# 📊 Bảng Điều Khiển Dự Báo Bán Hàng & Phân Tích Khách Hàng Thông Minh AI

<p align="center">
  <strong>Nền tảng Business Intelligence hiện đại kết hợp phân tích dự đoán với phân khúc khách hàng</strong><br>
  Xây dựng với Next.js, FastAPI, Prophet ML và K-Means Clustering
</p>

---

## 🚀 Overview - Tổng Quan

**Bảng Điều Khiển Dự Báo Bán Hàng AI (AI-Powered Sales Forecasting Dashboard)** là một nền tảng Business Intelligence toàn diện kết hợp:
- **Phân Tích Dự Đoán (Predictive Analytics)**: Dự báo bán hàng bằng AI sử dụng Facebook Prophet
- **Phân Tích Khách Hàng Thông Minh (Customer Intelligence)**: Phân tích RFM với phân cụm K-Means để phân khúc khách hàng
- **Trực Quan Hóa Tương Tác (Interactive Visualization)**: Biểu đồ và bộ lọc thời gian thực để khám phá dữ liệu

Hoàn hảo cho các nhà phân tích kinh doanh, nhà khoa học dữ liệu và đội ngũ sản phẩm cần cả hai thông tin **"Điều gì sẽ xảy ra?"** (dự báo) và **"Khách hàng của chúng ta là ai?"** (phân khúc).

---

## ✨ Key Features - Tính Năng Chính

### 📈 Sales Analytics & Forecasting - Phân Tích & Dự Báo Bán Hàng
- **Theo Dõi KPI Thời Gian Thực (Real-time KPI Tracking)**: Tổng Doanh Thu, Lợi Nhuận, Đơn Hàng, Chiết Khấu Trung Bình
- **Bộ Lọc Tương Tác (Interactive Filtering)**: Khoảng thời gian, Khu vực, Lựa chọn danh mục
- **Trực Quan Hóa Xu Hướng Bán Hàng (Sales Trend Visualization)**: Mô hình bán hàng hàng ngày với biểu đồ đường
- **Phân Tích Theo Danh Mục & Khu Vực (Category & Region Analysis)**: Biểu đồ cột và tròn cho phân phối
- **Dự Báo Bằng AI (AI Forecasting)**: Dự đoán bán hàng 30 ngày sử dụng Facebook Prophet với khoảng tin cậy

### 👥 Customer Intelligence - Phân Tích Khách Hàng Thông Minh
- **Phân Tích RFM (RFM Analysis)**: Tự động tính toán các chỉ số Recency (Gần đây), Frequency (Tần suất) và Monetary (Giá trị tiền tệ)
- **Phân Khúc Khách Hàng (Customer Segmentation)**: Phân cụm K-Means thành 4 nhóm:
  - **Khách Hàng Vàng (Champions)**: Người mua có giá trị cao, thường xuyên
  - **Khách Hàng Trung Thành (Loyalists)**: Khách hàng nhất quán, giá trị trung bình
  - **Có Nguy Cơ Rời Bỏ (Problem Children)**: Khách hàng trước đây hoạt động nhưng gần đây chưa mua hàng
  - **Khách Hàng Mới (New Customers)**: Tần suất và giá trị tiền tệ thấp
- **Trực Quan Hóa Tương Tác**:
  - Biểu đồ tròn phân phối phân khúc
  - Biểu đồ bong bóng RFM (Recency vs Monetary, kích thước theo Frequency)
  - Bảng thống kê phân khúc chi tiết

---

## 🛠 Tech Stack - Công Nghệ Sử Dụng

### Backend
- **FastAPI** - Framework web Python bất đồng bộ hiệu suất cao
- **Pandas** - Thao tác và phân tích dữ liệu
- **Prophet** - Thư viện dự báo chuỗi thời gian của Facebook
- **Scikit-learn** - Học máy (phân cụm K-Means)
- **NumPy** - Tính toán số học
- **Uvicorn** - Máy chủ ASGI

### Frontend
- **Next.js 16** - Framework React với App Router
- **TypeScript** - Phát triển an toàn kiểu dữ liệu
- **Chart.js** - Trực quan hóa dữ liệu tương tác
- **Tailwind CSS** - Styling hiện đại, responsive
- **Axios** - HTTP client cho các lời gọi API
- **Lucide React** - Thư viện icon đẹp

### Data - Dữ Liệu
- **SampleSuperstore.csv** - Bộ dữ liệu bán hàng bán lẻ với thông tin khách hàng

---

## 📁 Project Structure - Cấu Trúc Dự Án

```
AI-Powered-Sales-Forecasting-Dashboard/
├── backend/
│   ├── main.py              # Ứng dụng FastAPI với tất cả endpoints
│   ├── requirements.txt     # Các thư viện Python
│   └── test_main.py         # Kiểm thử backend
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Trang dashboard chính
│   │   ├── customers/
│   │   │   └── page.tsx     # Trang phân tích khách hàng (MỚI!)
│   │   ├── layout.tsx       # Layout gốc
│   │   └── globals.css      # Styles toàn cục
│   ├── components/
│   │   └── Dashboard.tsx    # Component dashboard chính
│   ├── lib/
│   │   └── api.ts           # Các hàm API client
│   └── package.json         # Các thư viện Node
├── data/
│   └── SampleSuperstore.csv # Bộ dữ liệu
└── knowledge/               # Tài nguyên học tập (MỚI!)
    ├── 01-backend.md
    ├── 02-frontend.md
    ├── 03-machine-learning.md
    └── 04-deployment.md
```

---

## 🎯 API Endpoints

### Sales Analytics - Phân Tích Bán Hàng
- `GET /api/filters` - Lấy các tùy chọn bộ lọc có sẵn
- `GET /api/kpis` - Lấy các chỉ số KPI (doanh thu, lợi nhuận, đơn hàng, chiết khấu)
- `GET /api/charts/sales-trend` - Dữ liệu xu hướng bán hàng hàng ngày
- `GET /api/charts/category-sales` - Doanh thu theo danh mục
- `GET /api/charts/region-sales` - Doanh thu theo khu vực
- `GET /api/forecast` - Dự báo bán hàng 30 ngày sử dụng Prophet

### Customer Intelligence - Phân Tích Khách Hàng Thông Minh
- `GET /api/customer-segmentation` - Phân tích RFM với phân cụm K-Means
- `GET /api/sales-heatmap` - Dữ liệu bán hàng hàng ngày cho trực quan hóa heatmap

---

## ▶️ Getting Started - Bắt Đầu

### Requirements - Yêu Cầu
- **Python 3.8+**
- **Node.js 18+**
- **npm hoặc yarn**

### Installation - Cài Đặt

#### 1. Clone Repository
```bash
git clone https://github.com/your-username/AI-Powered-Sales-Forecasting-Dashboard.git
cd AI-Powered-Sales-Forecasting-Dashboard
```
docker compose up -d --build
#### 2. Backend Setup - Thiết Lập Backend
```bash
cd backend
pip install -r requirements.txt
python main.py / uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend runs on **http://localhost:8000**


#### 3. Frontend Setup - Thiết Lập Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs on **http://localhost:3000**

#### 4. Truy cập pgAdmin để xem database

Mở trình duyệt và truy cập:
→ http://localhost:5050
Đăng nhập pgAdmin:
Email: admin@admin.com
Password: admin123

Thêm Server mới (Register Server):
General → Name: AI Sales Insight DB (tùy bạn đặt)
Connection tab:
Host name/address: postgres         
Port: 5432
Maintenance database: sales_dashboard 
Username: sales_user 
Password: 123456


Nhấn Save.

Nếu kết nối thành công, bạn sẽ thấy danh sách các bảng trong schema public.
Các bảng quan trọng cần xem trong project này:

users → danh sách người dùng
datasets
analysis_runs → các lần phân tích đã chạy
widgets → các insight được sinh ra (rất quan trọng để debug format insight)
chat_history
knowledge_chunks

Bạn có thể click chuột phải vào bảng → View/Edit Data → All Rows để xem dữ liệu.


### Quick Start Script (Windows)
```bash
# Chạy từ thư mục gốc dự án
start_app.bat
```

---

## 📖 How to Use - Hướng Dẫn Sử Dụng

### Dashboard Chính
1. Truy cập http://localhost:3000
2. Sử dụng bộ lọc để chọn:
   - Khoảng thời gian
   - Danh mục (Nội thất, Công nghệ, Văn phòng phẩm)
   - Khu vực (Đông, Tây, Bắc, Nam)
3. Xem các KPI và biểu đồ tương tác
4. Cuộn xuống để xem dự báo bán hàng bằng AI

### Phân Tích Khách Hàng (MỚI!)
1. Nhấp vào nút **"Customer Insights"** ở góc trên bên phải
2. Xem phân tích phân khúc khách hàng:
   - **Biểu Đồ Tròn**: Phân phối khách hàng qua các phân khúc
   - **Bảng Thống Kê**: Các chỉ số trung bình mỗi phân khúc
   - **Biểu Đồ Bong Bóng**: Trực quan hóa phân tích RFM
3. Sử dụng thông tin cho marketing mục tiêu:
   - **Khách Hàng Vàng**: Thưởng với chương trình khách hàng thân thiết
   - **Có Nguy Cơ Rời Bỏ**: Khởi chạy chiến dịch tái tương tác
   - **Khách Hàng Mới**: Triển khai quy trình giới thiệu
   - **Trung Thành**: Đề xuất cơ hội bán thêm

---

## 📚 Learning Resources - Tài Nguyên Học Tập

Kiểm tra thư mục **`knowledge/`** để có tài liệu học tập toàn diện bao gồm:
- Phát triển Backend với FastAPI và Python
- Phát triển Frontend với Next.js và TypeScript
- Học Máy (Prophet, K-Means)
- Chiến lược triển khai

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest test_main.py -v
```

### Frontend Linting
```bash
cd frontend
npm run lint
```

---

## 🚀 Deployment - Triển Khai

### Backend
- **Khuyến nghị (Recommended)**: PythonAnywhere (Có gói miễn phí)
- **Thay thế (Alternative)**: Heroku, Railway, Render

### Frontend
- **Khuyến nghị (Recommended)**: Vercel (Gói miễn phí với tối ưu hóa Next.js)
- **Thay thế (Alternative)**: Netlify, Cloudflare Pages

---

## 📈 Future Improvements - Cải Tiến Tương Lai

- [ ] Dự báo theo phân khúc (dự đoán doanh thu theo từng phân khúc khách hàng)
- [ ] Heatmap lịch cho tính thời vụ bán hàng
- [ ] Biểu đồ Sankey cho trực quan hóa luồng bán hàng
- [ ] Bộ lọc nâng cao (kết hợp phân khúc khách hàng với khu vực)
- [ ] Xuất dữ liệu phân khúc khách hàng ra CSV
- [ ] Cảnh báo email cho khách hàng có nguy cơ rời bỏ

---

## 🤝 Contributing - Đóng Góp

Chào đón các đóng góp! Vui lòng gửi Pull Request.

---

## 📄 License - Giấy Phép

Dự án này là mã nguồn mở và có sẵn theo Giấy phép MIT.

---

## 🌟 Thank You - Lời Cảm Ơn

- **Facebook Prophet** cho dự báo chuỗi thời gian
- **Scikit-learn** cho các thuật toán học máy
- **Next.js** và **FastAPI** teams cho các framework xuất sắc
- **Chart.js** cho các trực quan hóa đẹp

---

## 📧 Contact - Liên Hệ

Để đặt câu hỏi hoặc phản hồi, vui lòng mở một issue trên GitHub.

---

<p align="center">Được tạo với ❤️ cho việc ra quyết định dựa trên dữ liệu</p>
