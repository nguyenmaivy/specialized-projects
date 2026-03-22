# 🚀 Hướng Dẫn Setup - AI-Powered Sales Forecasting Dashboard

**Phiên bản:** v2.0.0 | **Ngày cập nhật:** 22/03/2026

---

## 📋 Yêu Cầu Hệ Thống

- **Python** 3.10+
- **Node.js** 18+ (cho frontend)
- **Docker** (optional, cho deployment)

---

## ⚡ Setup Nhanh (Local Development)

### Bước 1: Clone dự án
```bash
git clone <repo-url>
cd AI-Powered-Sales-Forecasting-Dashboard
```

### Bước 2: Setup Backend

```bash
# Cài thư viện Python
cd backend
pip install -r requirements.txt

# Copy file env (tùy chỉnh nếu cần)
cp .env.example .env

# Chạy server
python main.py
# hoặc
uvicorn backend.main:app --reload --port 8000
```

**Backend chạy tại:** `http://localhost:8000`  
**API Docs (Swagger):** `http://localhost:8000/docs`

### Bước 3: Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

**Frontend chạy tại:** `http://localhost:3000`

### Bước 4: Kiểm tra

```bash
# Kiểm tra backend health
curl http://localhost:8000/health

# Chạy tests (từ thư mục gốc)
cd ..
python -m pytest backend/test_main.py -v
```

---

## 🔐 Authentication

### Cấu Hình

Auth mặc định tắt (`AUTH_REQUIRED=false`). Bật lên bằng cách sửa `.env`:

```
AUTH_REQUIRED=true
SECRET_KEY=your-strong-secret-key-here
TOKEN_EXPIRE_MINUTES=60
```

### Tài Khoản Mặc Định

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | admin |

### Sử Dụng API với Auth

**1. Đăng nhập lấy token:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCAiYWxn...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**2. Gọi API với token:**
```bash
curl http://localhost:8000/api/kpis \
  -H "Authorization: Bearer <access_token>"
```

**3. Tạo user mới (chỉ admin):**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"username": "newuser", "password": "password123", "role": "viewer"}'
```

**Roles:** `viewer` (xem), `editor` (sửa), `admin` (quản lý)

---

## ⚙️ Cấu Hình Environment Variables

File `.env` trong `backend/`:

| Biến | Mặc định | Mô tả |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8080` | CORS origins (phân cách bằng dấu `,`) |
| `AUTH_REQUIRED` | `false` | Bật/tắt yêu cầu JWT cho `/api/*` |
| `SECRET_KEY` | (mặc định dev key) | JWT secret key (**bắt buộc đổi cho production**) |
| `TOKEN_EXPIRE_MINUTES` | `60` | Thời gian hết hạn token (phút) |
| `RATE_LIMIT` | `100/minute` | Giới hạn request per IP |

### 🔀 So Sánh: `AUTH_REQUIRED=false` vs `AUTH_REQUIRED=true`

#### Trường hợp 1: `AUTH_REQUIRED=false` (Mặc định)

```env
AUTH_REQUIRED=false
```

| Đặc điểm | Mô tả |
|---|---|
| **Frontend** | Vào thẳng Dashboard, **không hiện trang Login** |
| **API `/api/*`** | Truy cập tự do, **không cần token** |
| **Auth endpoints** | Vẫn hoạt động (`/auth/login`, `/auth/register`...) nhưng không bắt buộc |
| **Phù hợp** | Development, demo, môi trường nội bộ |

**Ví dụ gọi API:**
```bash
# Không cần token
curl http://localhost:8000/api/kpis
curl http://localhost:8000/api/filters
```

---

#### Trường hợp 2: `AUTH_REQUIRED=true`

```env
AUTH_REQUIRED=true
SECRET_KEY=your-strong-secret-key-here
TOKEN_EXPIRE_MINUTES=60
```

| Đặc điểm | Mô tả |
|---|---|
| **Frontend** | Hiện **trang Login** trước, phải đăng nhập mới vào Dashboard |
| **API `/api/*`** | Trả **401 Unauthorized** nếu không có JWT token |
| **Header** | Hiển thị **user badge** (username + role) và nút **Logout** |
| **Phù hợp** | Production, nhiều người dùng, bảo mật |

**Ví dụ gọi API:**
```bash
# Bước 1: Lấy token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Bước 2: Dùng token để gọi API
curl http://localhost:8000/api/kpis \
  -H "Authorization: Bearer <access_token>"
```

> ⚠️ **Lưu ý:** Sau khi thay đổi `.env`, cần **restart backend** (`python main.py`) để áp dụng.

---

## 📡 API Endpoints (Đã Implement ✅)

### Public (không cần auth)
| Status | Method | Path | Mô tả |
|---|---|---|---|
| ✅ | GET | `/` | Welcome message |
| ✅ | GET | `/health` | Health check (status, version, records, auth status) |

### Auth (luôn hoạt động)
| Status | Method | Path | Mô tả |
|---|---|---|---|
| ✅ | POST | `/auth/login` | Đăng nhập, trả JWT token |
| ✅ | POST | `/auth/register` | Tạo user mới (chỉ admin) |
| ✅ | GET | `/auth/me` | Thông tin user hiện tại |
| ✅ | GET | `/auth/users` | Danh sách users (chỉ admin) |
| ✅ | PUT | `/auth/change-password` | Đổi mật khẩu (user đang đăng nhập) |
| ✅ | DELETE | `/auth/users/{username}` | Xóa user (chỉ admin, không xóa được admin) |
| ✅ | POST | `/auth/logout` | Đăng xuất (client xóa token) |

### Data API (Protected khi `AUTH_REQUIRED=true`)
| Status | Method | Path | Mô tả |
|---|---|---|---|
| ✅ | GET | `/api/filters` | Danh sách categories, regions, date range |
| ✅ | GET | `/api/kpis` | KPI tổng hợp (sales, profit, orders, discount) |
| ✅ | GET | `/api/charts/sales-trend` | Doanh thu theo thời gian |
| ✅ | GET | `/api/charts/category-sales` | Doanh thu theo danh mục |
| ✅ | GET | `/api/charts/region-sales` | Doanh thu theo khu vực |
| ✅ | GET | `/api/forecast` | Dự báo doanh thu 30 ngày (Prophet AI) |
| ✅ | GET | `/api/customer-segmentation` | Phân khúc khách hàng RFM (KMeans) |
| ✅ | GET | `/api/sales-heatmap` | Dữ liệu heatmap lịch bán hàng |
| ✅ | GET | `/api/export/csv` | Xuất dữ liệu đã lọc dạng CSV |

### Query Parameters (áp dụng cho tất cả `/api/*`)
| Param | Ví dụ | Mô tả |
|---|---|---|
| `category` | `?category=Furniture` | Lọc theo category (nhiều: `&category=Technology`) |
| `region` | `?region=South` | Lọc theo region (nhiều: `&region=West`) |
| `start_date` | `?start_date=2014-01-03` | Từ ngày (YYYY-MM-DD) |
| `end_date` | `?end_date=2017-12-30` | Đến ngày (YYYY-MM-DD) |

### Frontend Pages
| Status | Path | Mô tả |
|---|---|---|
| ✅ | `/` | Dashboard chính (KPIs, charts, forecast, heatmap) |
| ✅ | `/customers` | Customer Intelligence (RFM, segmentation) |
| ✅ | Login Page | Trang đăng nhập (hiện khi `AUTH_REQUIRED=true`) |

---

## 🐳 Docker Deployment

### Chạy với Docker Compose

```bash
# Build và chạy tất cả services
docker-compose up --build

# Chạy nền
docker-compose up --build -d

# Xem logs
docker-compose logs -f backend

# Dừng
docker-compose down
```

### Services

| Service | URL | Port |
|---|---|---|
| Backend API | `http://localhost:8000` | 8000 |
| Frontend | `http://localhost:3000` | 3000 |

### MongoDB & Redis (Optional)

Trong `docker-compose.yml`, uncomment các services `mongo` và `redis` khi sẵn sàng.

---

## 🧪 Chạy Tests

```bash
# Tất cả tests
python -m pytest backend/test_main.py -v

# Chạy 1 class
python -m pytest backend/test_main.py::TestAuthEndpoints -v

# Chạy 1 test cụ thể
python -m pytest backend/test_main.py::TestAuthEndpoints::test_login_success -v

# Xem coverage (cần cài pytest-cov)
python -m pytest backend/test_main.py --cov=backend --cov-report=term-missing
```

**Test coverage hiện tại: 101 tests, 16 test classes**

---

## 📂 Cấu Trúc Dự Án

```
AI-Powered-Sales-Forecasting-Dashboard/
├── backend/
│   ├── main.py              # FastAPI app (v2.0)
│   ├── auth.py              # JWT authentication module
│   ├── conftest.py           # Pytest shared fixtures
│   ├── test_main.py          # 101 test cases
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile            # Backend Docker image
│   ├── .env.example          # Environment template
│   └── logs/                 # Log files (auto-created)
├── frontend/
│   ├── app/                  # Next.js pages
│   ├── components/           # React components
│   ├── lib/                  # API client
│   ├── Dockerfile            # Frontend Docker image
│   └── package.json
├── data/
│   └── SampleSuperstore.csv  # Dataset
├── legacy/
│   └── IMPROVEMENTS_HISTORY.md  # Change log
├── docker-compose.yml        # Docker orchestration
├── SETUP_GUIDE.md            # This file
└── README.md
```
