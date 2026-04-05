# 🚀 Hướng Dẫn Setup - AI-Powered Sales Forecasting Dashboard

**Phiên bản:** v2.1.0 | **Ngày cập nhật:** 05/04/2026 | **Trạng thái:** ✅ Stable

---

## ⚡ Quick Start: Hướng Dẫn Từng Bước (Cho Người Mới)

### 📌 PHƯƠNG PHÁP VÀ ĐƠNGIẢN NHẤT (Windows)

**Chỉ 1 click là xong!** Nếu bạn dùng Windows:

1️⃣ **Mở PowerShell/CMD tại thư mục dự án**
   ```
   D:\Nam-4\HK2\DoAnChuyenNganh-Dat\DO-AN-CHUYEN-NGANH\AI-Powered-Sales-Forecasting-Dashboard
   ```

2️⃣ **Chạy file batch:**
   ```bash
   start_app.bat
   ```

3️⃣ **Chờ ~3-5 phút**, 2 cửa sổ terminal sẽ tự mở:
   - Một cho Backend (port 8000)
   - Một cho Frontend (port 3000)

4️⃣ **Truy cập ứng dụng:**
   ```
   Backend API: http://localhost:8000
   Frontend: http://localhost:3000
   API Docs: http://localhost:8000/docs
   ```

✅ **XONG!** Bạn đã setup thành công!

---

### 📌 PHƯƠNG PHÁP TỪNG BƯỚC (macOS/Linux/Windows nâng cao)

Nếu `start_app.bat` không hoạt động hoặc bạn muốn control chi tiết, làm theo:

#### **BƯỚC 1️⃣: Kiểm tra điều kiện tiên quyết (5 phút)**

Mở PowerShell/Terminal và chạy các lệnh này:

```bash
# Kiểm tra Python
python --version
# ✅ Phải >= Python 3.10

# Kiểm tra Node.js
node -v
# ✅ Phải >= v18

# Kiểm tra npm
npm -v
# ✅ Phải >= 9
```

**Nếu thiếu cái nào:**
- Python: tải từ https://www.python.org/downloads/
- Node.js: tải từ https://nodejs.org/
- Git: tải từ https://git-scm.com/

---

#### **BƯỚC 2️⃣: Clone dự án (2 phút)**

```bash
# Copy code này vào PowerShell
git clone <repo-url>
cd AI-Powered-Sales-Forecasting-Dashboard

# Xác nhận bạn ở đúng thư mục
cd  # Sẽ hiện: D:\...\AI-Powered-Sales-Forecasting-Dashboard
```

---

#### **BƯỚC 3️⃣: Setup Backend (5 phút)**

```bash
# Vào thư mục backend
cd backend

# Tạo virtual environment (giống như hộp riêng cho Python)
python -m venv venv

# Kích hoạt virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Cài đặt Python libraries
pip install -r requirements.txt
# ⏳ Chờ ~1-2 phút tải packages

# Tạo file .env (config)
# Trên Windows (PowerShell):
Copy-Item .env.example .env
# Trên macOS/Linux:
cp .env.example .env
```

**Kiểm tra Backend:**
```bash
# Chạy Backend
python -m uvicorn main:app --reload --port 8000

# Mở browser: http://localhost:8000/health
# ✅ Bạn sẽ thấy: {"status": "healthy", "version": "2.1.0", ...}
```

⏸️ **Hãy giữ terminal này mở!** Đừng Ctrl+C. Mở terminal mới nếu cần.

---

#### **BƯỚC 4️⃣: Setup Frontend (5 phút) - Terminal mới**

```bash
# Mở PowerShell/Terminal MỚI (giữ backend chạy)

# Về gốc dự án (từ backend lên)
cd ..

# Vào thư mục frontend
cd frontend

# Cài npm packages
npm install
# ⏳ Chờ ~1-2 phút

# Chạy Frontend
npm run dev

# Mở browser: http://localhost:3000
# ✅ Bạn sẽ thấy Dashboard!
```

⏸️ **Giữ terminal này mở!**

---

#### **BƯỚC 5️⃣: Kiểm tra ứng dụng (2 phút)**

Mở browser và truy cập lần lượt:

✅ **Frontend Dashboard:** http://localhost:3000
   - Bạn sẽ thấy: KPIs, Charts, Sales Forecast

✅ **Backend Swagger Docs:** http://localhost:8000/docs
   - Bạn sẽ thấy: Danh sách tất cả APIs

✅ **Health Check:** http://localhost:8000/health
   - Bạn sẽ thấy: JSON status

---

### 📌 PHƯƠNG PHÁP DOCKER (Nâng cao - Production)

Nếu bạn muốn setup bằng Docker (bao gồm PostgreSQL database):

#### **BƯỚC 1️⃣: Cài Docker Desktop**

Tải từ: https://www.docker.com/products/docker-desktop

Kiểm tra:
```bash
docker --version
docker-compose --version
```

#### **BƯỚC 2️⃣: Chạy Docker Compose**

```bash
# Tại thư mục gốc dự án
docker-compose up --build -d

# Chờ ~2-3 phút
```

#### **BƯỚC 3️⃣: Kiểm tra services**

```bash
# Xem status
docker-compose ps

# Xem logs
docker-compose logs -f

# Truy cập apps
Frontend: http://localhost:3000
Backend: http://localhost:8000
Database: localhost:5432 (PostgreSQL)
```

#### **BƯỚC 4️⃣: Dừng Docker**

```bash
docker-compose down
```

---

## 📋 Yêu Cầu Hệ Thống

### Requirement Bắt Buộc
| Công Nghệ | Phiên Bản | Lưu Ý |
|-----------|----------|-------|
| **Python** | 3.10+ | Dùng `python --version` để kiểm tra |
| **Node.js** | 18+ | Dùng `node -v` để kiểm tra |
| **npm** | 9+ | Cài kèm Node.js |
| **Git** | 2.0+ | (Optional, nếu clone repo) |

### Optional (cho Docker deployment)
- **Docker** 24+
- **Docker Compose** 2.0+

### Dung lượng ổ cứng tối thiểu
- **Development:** ~1.5 GB (Python packages + Node modules)
- **Production:** ~2 GB (bao gồm data, logs, database)

---

## ⚡ Tùy Chọn Setup

Dự án hỗ trợ **3 cách setup**:

| Phương Pháp | Thời Gian | Độ Phức Tạp | Phù Hợp |
|-----------|----------|-----------|---------|
| **[Nhanh (1 lệnh)](#phương-pháp-và-đơngiản-nhất-windows)** | ~5 phút | Rất dễ | Tất cả (Windows recommended) |
| **[Từng bước](#phương-pháp-từng-bước-macosulinuxwindows-nâng-cao)** | ~20 phút | Dễ | macOS, Linux, Windows |
| **[Docker](#phương-pháp-docker-nâng-cao---production)** | ~10 phút | Trung bình | Production, CI/CD |

---

## 🔥 Setup Nhanh (start_app.bat)

### Dành cho Windows Users

App có sẵn script `start_app.bat` để setup và chạy toàn bộ ứng dụng một lệnh:

```bash
start_app.bat
```

**Script này sẽ:**
1. ✅ Cài đặt Python packages từ `backend/requirements.txt`
2. ✅ Cài đặt npm packages từ `frontend/package.json`
3. ✅ Khởi động Backend API (Uvicorn) trên port 8000
4. ✅ Khởi động Frontend (Next.js) trên port 3000
5. ✅ Mở 2 cửa sổ terminal riêng cho mỗi service

**Kết quả:**
```
Backend chạy tại: http://localhost:8000
Frontend chạy tại: http://localhost:3000
API Docs (Swagger): http://localhost:8000/docs
```

> **Lưu ý:** Đảm bảo Python và Node.js đã được cài đặt trong PATH trước khi chạy script.

---

## 📝 Setup Chi Tiết

### Phương Pháp 1: Setup Backend trước

#### Bước 1: Điều kiện tiên quyết

```bash
# Kiểm tra Python version
python --version
# Output: Python 3.10.x hoặc cao hơn

# Kiểm tra Node.js version
node -v
# Output: v18.x.x hoặc cao hơn

# Kiểm tra npm version
npm -v
# Output: 9.x.x hoặc cao hơn
```

#### Bước 2: Clone & Cấu Hình Backend

```bash
# Clone repository
git clone <repo-url>
cd AI-Powered-Sales-Forecasting-Dashboard

# Di chuyển vào thư mục backend
cd backend

# Tạo virtual environment (recommended)
python -m venv venv

# Kích hoạt virtual environment
# Trên Windows:
venv\Scripts\activate
# Trên macOS/Linux:
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt

# Copy file .env template (nếu có)
# cp .env.example .env   # Trên macOS/Linux
# copy .env.example .env # Trên Windows (hoặc dùng GUI)
```

#### Bước 3: Kiểm tra Database (PostgreSQL - Optional)

Nếu muốn sử dụng PostgreSQL (mặc định app dùng SQLite):

```bash
# Tạo database
# Giả sử có PostgreSQL chạy trên local
psql -U postgres -h localhost -c "CREATE DATABASE sales_dashboard;"
psql -U postgres -h localhost -c "CREATE USER sales_user WITH PASSWORD '123456';"
psql -U postgres -h localhost -c "ALTER ROLE sales_user WITH LOGIN;"
```

Rồi cập nhật `.env`:
```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sales_dashboard
POSTGRES_USER=sales_user
POSTGRES_PASSWORD=123456
```

#### Bước 4: Chạy Backend

```bash
# Từ thư mục backend/
python -m uvicorn main:app --reload --port 8000

# Hoặc nếu có script:
python main.py
```

**Output khi thành công:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

#### Bước 5: Kiểm tra Backend

Mở browser và truy cập:
- **API Swagger Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/health`

```bash
# Hoặc dùng curl
curl http://localhost:8000/health

# Output:
# {
#   "status": "healthy",
#   "version": "2.1.0",
#   "records": 9994,
#   "auth_required": false
# }
```

---

### Phương Pháp 2: Setup Frontend

#### Bước 1: Mở terminal mới

```bash
# Từ thư mục gốc (AI-Powered-Sales-Forecasting-Dashboard)
cd frontend

# Cài npm packages
npm install
# Hoặc dùng yarn
yarn install
```

#### Bước 2: Config API Endpoint (nếu cần)

File: `frontend/lib/api.ts`

```typescript
// localhost development (mặc định)
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Nếu deploy ra remote, set environment variable:
# .env.local
NEXT_PUBLIC_API_URL=https://api.example.com
```

#### Bước 3: Chạy Frontend

```bash
# Development mode (hot reload)
npm run dev

# Production build
npm run build
npm start
```

**Output khi thành công:**
```
- Ready in 1.5s
- Local:        http://localhost:3000
- Environments: .env.local
```

#### Bước 4: Kiểm tra Frontend

Mở browser: `http://localhost:3000`

---

## 🔐 Cấu Hình Authentication

### Mặc Định (AUTH_REQUIRED=false)

```env
AUTH_REQUIRED=false
```

| Tính Năng | Trạng Thái |
|-----------|-----------|
| Frontend | Vào thẳng Dashboard (không hiện trang Login) |
| API `/api/*` | Truy cập tự do, không cần token |
| Auth endpoints | Vẫn hoạt động nhưng không bắt buộc |
| Phù hợp | Development, demo, nội bộ |

**Ví dụ:**
```bash
# API không cần token
curl http://localhost:8000/api/kpis
curl http://localhost:8000/api/filters
```

### Bật Authentication (AUTH_REQUIRED=true)

```env
AUTH_REQUIRED=true
SECRET_KEY=your-super-strong-secret-key-min-32-chars
TOKEN_EXPIRE_MINUTES=60
RATE_LIMIT=100/minute
```

| Tính Năng | Trạng Thái |
|-----------|-----------|
| Frontend | Hiện trang Login (bắt buộc đăng nhập) |
| API `/api/*` | Trả 401 nếu không có JWT token |
| Header | Hiển thị User Badge + Logout button |
| Database | Lưu user & session (PostgreSQL/SQLite) |

**Tài Khoản Mặc Định:**

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | admin |

**Sử Dụng API:**

```bash
# Bước 1: Đăng nhập
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCAiYWxn...",
#   "token_type": "bearer",
#   "expires_in": 3600
# }

# Bước 2: Sử dụng token
curl http://localhost:8000/api/kpis \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCAiYWxn..."
```

---

### Users Management (Admin Only)

```bash
# Lấy danh sách users
curl http://localhost:8000/auth/users \
  -H "Authorization: Bearer <admin_token>"

# Tạo user mới
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "username": "john_doe",
    "password": "secure_password",
    "role": "viewer"
  }'

# Đổi mật khẩu (user hiện tại)
curl -X PUT http://localhost:8000/auth/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <user_token>" \
  -d '{
    "old_password": "old123",
    "new_password": "new123"
  }'

# Xóa user
curl -X DELETE http://localhost:8000/auth/users/john_doe \
  -H "Authorization: Bearer <admin_token>"
```

**Roles:**
- `admin` - Quản lý users, ads, settings
- `editor` - Xem & sửa dữ liệu
- `viewer` - Chỉ xem dữ liệu
---

## ⚙️ Environment Variables (.env)

### Vị Trí File
```
backend/.env
```

### Biến Chính

| Biến | Mặc Định | Kiểu | Mô Tả |
|------|---------|------|-------|
| `AUTH_REQUIRED` | `false` | bool | Bật/tắt xác thực JWT |
| `SECRET_KEY` | `dev-key` | str | JWT signing key (min 32 chars cho production) |
| `TOKEN_EXPIRE_MINUTES` | `60` | int | Thời gian token hết hạn (phút) |
| `ALLOWED_ORIGINS` | `http://localhost:3000,http://localhost:8080` | str | CORS origins (phân cách dấu `,`) |
| `RATE_LIMIT` | `100/minute` | str | Giới hạn requests per IP |

### Database Configuration

| Biến | Mặc Định | Mô Tả |
|------|---------|-------|
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `sales_dashboard` | Database name |
| `POSTGRES_USER` | `sales_user` | DB user |
| `POSTGRES_PASSWORD` | `123456` | DB password ⚠️ **Đổi cho production** |

### AI/ML Configuration

| Biến | Mặc Định | Mô Tả |
|------|---------|-------|
| `OPENROUTER_API_KEY` | `` | OpenRouter API key (tùy chọn) |
| `OPENROUTER_MODEL` | `nvidia/nemotron-3-super-120b-a12b:free` | LLM model dùng cho insights |

### Template .env

```env
# ═══ AUTHENTICATION ═══
AUTH_REQUIRED=false
SECRET_KEY=your-super-secret-key-change-this-in-production
TOKEN_EXPIRE_MINUTES=60

# ═══ CORS ═══
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# ═══ RATE LIMITING ═══
RATE_LIMIT=100/minute

# ═══ DATABASE (PostgreSQL) ═══
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sales_dashboard
POSTGRES_USER=sales_user
POSTGRES_PASSWORD=123456

# ═══ AI/ML ═══
OPENROUTER_API_KEY=sk-or-....
OPENROUTER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
```

> **⚠️ Lưu ý:** Sau khi thay đổi `.env`, **restart backend** để áp dụng.

---

## 📡 API Endpoints Reference

### Health & Status

| Method | Endpoint | Auth | Return | Mô Tả |
|--------|----------|------|--------|-------|
| GET | `/` | ❌ | Welcome | Welcome message |
| GET | `/health` | ❌ | JSON | Health check (status, version, records, auth) |

### Authentication (Luôn Hoạt Động)

| Method | Endpoint | Auth | Request | Mô Tả |
|--------|----------|------|---------|-------|
| POST | `/auth/login` | ❌ | `{username, password}` | Đăng nhập, trả token |
| POST | `/auth/register` | ✅ (admin) | `{username, password, role}` | Tạo user (chỉ admin) |
| GET | `/auth/me` | ✅ | - | Thông tin user hiện tại |
| GET | `/auth/users` | ✅ (admin) | - | Danh sách tất cả users |
| PUT | `/auth/change-password` | ✅ | `{old_password, new_password}` | Đổi mật khẩu |
| DELETE | `/auth/users/{username}` | ✅ (admin) | - | Xóa user |
| POST | `/auth/logout` | ✅ | - | Đăng xuất |

### Data API (Protected nếu `AUTH_REQUIRED=true`)

| Method | Endpoint | Query Params | Mô Tả |
|--------|----------|--------------|-------|
| GET | `/api/filters` | - | Danh sách categories, regions, date range |
| GET | `/api/kpis` | `category`, `region`, `start_date`, `end_date` | KPI tổng hợp |
| GET | `/api/charts/sales-trend` | Filters | Doanh thu theo thời gian |
| GET | `/api/charts/category-sales` | Filters | Doanh thu theo danh mục |
| GET | `/api/charts/region-sales` | Filters | Doanh thu theo khu vực |
| GET | `/api/forecast` | Filters | Dự báo 30 ngày (Prophet) |
| GET | `/api/customer-segmentation` | Filters | Phân khúc khách hàng RFM |
| GET | `/api/sales-heatmap` | Filters | Dữ liệu heatmap lịch |
| GET | `/api/export/csv` | Filters | Xuất CSV |

### Query Parameters

Áp dụng cho tất cả `/api/*` endpoints:

```
?category=Furniture&region=South&start_date=2014-01-03&end_date=2017-12-30
```

| Param | Ví Dụ | Mô Tả | Bắt Buộc |
|-------|-------|-------|---------|
| `category` | `Furniture` | Lọc theo category (có thể lặp lại) | ❌ |
| `region` | `South` | Lọc theo region (có thể lặp lại) | ❌ |
| `start_date` | `2014-01-03` | Từ ngày (YYYY-MM-DD) | ❌ |
| `end_date` | `2017-12-30` | Đến ngày (YYYY-MM-DD) | ❌ |

---

## 🎨 Frontend Pages

| URL | Mô Tả | Tính Năng |
|-----|-------|----------|
| `/` | Dashboard chính | KPIs, charts, forecast, heatmap |
| `/customers` | Customer Intelligence | RFM analysis, segmentation |
| `/settings` | Settings (nếu auth on) | User management, preferences |

---

## 🐳 Setup Docker

### Docker Compose (Recommended)

Dự án có sẵn `docker-compose.yml` với các services:

```bash
# Build & start tất cả services
docker-compose up --build

# Chạy nền
docker-compose up -d --build

# Xem logs real-time
docker-compose logs -f

# Xem logs backend
docker-compose logs -f backend

# Dừng services
docker-compose down

# Dừng & xóa volumes (cảnh báo: xóa data!)
docker-compose down -v
```

### Services trong docker-compose.yml

| Service | Image | URL | Port | Mô Tả |
|---------|-------|-----|------|-------|
| **postgres** | postgres:16-alpine | - | 5432 | Database |
| **backend** | ./backend (build local) | http://localhost:8000 | 8000 | FastAPI server |
| **frontend** | - (chạy npm) | http://localhost:3000 | 3000 | Next.js app |

### Environment Setup trong Docker

```yaml
environment:
  - POSTGRES_DB=sales_dashboard
  - POSTGRES_USER=sales_user
  - POSTGRES_PASSWORD=123456
  - AUTH_REQUIRED=false
  - ALLOWED_ORIGINS=http://localhost:3000
```

### Build Individual Services

```bash
# Build backend image
docker build -t sales-backend:2.1.0 ./backend

# Build frontend image
docker build -t sales-frontend:2.1.0 ./frontend

# Run backend container
docker run -p 8000:8000 -e AUTH_REQUIRED=false sales-backend:2.1.0

# Run frontend container  
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8000 sales-frontend:2.1.0
```

---

## 🧪 Testing

### Chạy Unit Tests

```bash
# Tất cả tests
pytest backend/test_main.py -v

# Tests cụ thể
pytest backend/test_main.py::TestAuthEndpoints -v

# Single test
pytest backend/test_main.py::TestAuthEndpoints::test_login_success -v

# Với coverage
pytest backend/test_main.py --cov=backend --cov-report=term-missing
```

### Test Coverage

```
📊 Current Test Coverage:
- Total Tests: 101
- Test Classes: 16
- Coverage: Chi tiết xem pytest report
```

### Manual Testing

**Health Check:**
```bash
curl http://localhost:8000/health -s | jq
```

**Test API Endpoint:**
```bash
# Lấy filters
curl http://localhost:8000/api/filters -s | jq

# Lấy KPIs
curl "http://localhost:8000/api/kpis?category=Furniture" -s | jq

# Lấy forecast
curl http://localhost:8000/api/forecast -s | jq
```

---

## 📁 Cấu Trúc Dự Án Chi Tiết

```
AI-Powered-Sales-Forecasting-Dashboard/
│
├── 📄 SETUP_GUIDE.md           ← You are here
├── 📄 README.md                 ← Project overview
├── 📄 docker-compose.yml        ← Docker configuration
├── 📄 start_app.bat             ← Quick start (Windows)
├── 📄 analyze_data.py           ← Data analysis utility
│
├── 🔧 backend/
│   ├── main.py                  ← FastAPI application (v2.1)
│   ├── auth.py                  ← JWT authentication module
│   ├── db.py                    ← Database connection
│   ├── conftest.py              ← Pytest fixtures
│   ├── test_main.py             ← 101 unit tests
│   ├── requirements.txt         ← Python dependencies
│   ├── Dockerfile               ← Docker image
│   ├── .env.example             ← Environment template
│   └── logs/                    ← Application logs
│
├── 🎨 frontend/
│   ├── app/
│   │   ├── page.tsx             ← Main dashboard page
│   │   ├── layout.tsx           ← Root layout
│   │   ├── globals.css          ← Global styles
│   │   ├── customers/
│   │   │   └── page.tsx         ← Customer intelligence page
│   │   └── settings/
│   │       └── page.tsx         ← Settings page
│   ├── components/
│   │   ├── Dashboard.tsx        ← Main dashboard component
│   │   ├── LoginPage.tsx        ← Login component
│   │   ├── ChartInsightPanel.tsx ← Chart insights
│   │   └── CalendarHeatmap.tsx  ← Heatmap component
│   ├── lib/
│   │   ├── api.ts               ← API client
│   │   ├── auth-api.ts          ← Auth API client
│   │   └── auth-context.tsx     ← Auth context provider
│   ├── public/                  ← Static assets
│   ├── package.json             ← NPM dependencies
│   ├── tsconfig.json            ← TypeScript config
│   ├── next.config.ts           ← Next.js config
│   ├── Dockerfile               ← Docker image
│   └── ESLint configs           ← Code quality
│
├── 📊 data/
│   ├── SampleSuperstore.csv     ← Dataset (9994 records)
│   └── your_final_dataset.csv   ← Processed data
│
├── 🧹 Cleaned_Data/
│   ├── cleaned_sales.csv
│   ├── cleaned_superstore_data.csv
│   ├── category_profit_summary.csv
│   └── top_10_products_by_sales.csv
│
├── 📚 knowledge/
│   ├── README.md                ← Learning resources
│   ├── PRD.md                   ← Product requirements
│   ├── implementation_plan.md   ← Implementation roadmap
│   ├── project_analysis.md      ← Architecture analysis
│   ├── ai-insight-spec.md       ← AI feature specs
│   ├── 01-backend.md            ← Backend guide
│   ├── 02-frontend.md           ← Frontend guide
│   ├── 03-machine-learning.md  ← ML algorithms
│   └── 04-deployment.md         ← Deployment guide
│
└── 🏛️ legacy/
    ├── ai-powered-sales-forecasting-dashboard.ipynb
    └── app.py (v1.0)
```

---

## 🔧 Troubleshooting

### Backend Issues

#### ❌ `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Cài lại dependencies
cd backend
pip install -r requirements.txt --upgrade
```

#### ❌ `Port 8000 already in use`
```bash
# Solution 1: Tìm process chiếm port
lsof -i :8000          # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Solution 2: Dùng port khác
python -m uvicorn main:app --port 8001
```

#### ❌ `Connection refused (Database)`
```bash
# Solution 1: Kiểm tra PostgreSQL running
# Solution 2: Dùng SQLite (mặc định)
# Solution 3: Config .env với host/port đúng
```

#### ❌ `JWT Secret Key error`
```bash
# Solution: .env phải có SECRET_KEY (min 32 chars)
SECRET_KEY=your-super-secret-key-that-is-long-enough-32-chars
```

### Frontend Issues

#### ❌ `Cannot GET /api/...`
```bash
# Solution 1: Kiểm tra backend chạy (port 8000)
# Solution 2: Kiểm tra NEXT_PUBLIC_API_URL env
# Solution 3: CORS configuration trong backend
```

#### ❌ `npm install fails`
```bash
# Solution 1: Xóa node_modules & package-lock.json
rm -rf node_modules package-lock.json  # macOS/Linux
rmdir /s /q node_modules & del package-lock.json  # Windows

# Solution 2: Cài lại
npm install

# Solution 3: Dùng npm cache clean
npm cache clean --force
npm install
```

#### ❌ `Tailwind CSS not loading`
```bash
# Solution: Build Tailwind
npm run build

# Hoặc dev mode với watch
npm run dev
```

### Docker Issues

#### ❌ `docker-compose command not found`
```bash
# Solution: Cập nhật Docker
docker --version  # Min 24.0
docker-compose --version  # Min 2.0
```

#### ❌ `Container exits immediately`
```bash
# Solution: Xem logs
docker-compose logs backend
docker logs <container_name>
```

---

## 📋 Data Dictionary

### SampleSuperstore.csv

| Column | Type | Range | Mô Tả |
|--------|------|-------|-------|
| `Row ID` | int | 1-9994 | Unique ID |
| `Order ID` | str | - | Order identifier |
| `Order Date` | date | 2014-2017 | Ngày đặt hàng |
| `Ship Date` | date | 2014-2017 | Ngày giao hàng |
| `Ship Mode` | str | Same Day, First Class, Standard | Loại vận chuyển |
| `Customer ID` | str | - | Customer identifier |
| `Customer Name` | str | - | Tên khách hàng |
| `Segment` | str | Consumer, Corporate, Home Office | Phân khúc khách |
| `Country` | str | United States | Quốc gia |
| `City` | str | - | Thành phố |
| `State` | str | - | Bang/Vùng |
| `Postal Code` | int | - | Mã bưu điện |
| `Region` | str | South, East, Central, West | Khu vực |
| `Product ID` | str | - | Product identifier |
| `Category` | str | Furniture, Office Supplies, Technology | Danh mục |
| `Sub-Category` | str | 17 values | Danh mục con |
| `Product Name` | str | - | Tên sản phẩm |
| `Sales` | float | 0.44 - 22638.48 | Doanh số bán hàng |
| `Quantity` | int | 1-14 | Số lượng |
| `Discount` | float | 0.0 - 0.2 | Chiết khấu (0-20%) |
| `Profit` | float | -6626 - 8399.98 | Lợi nhuận |

---

## 🚀 Next Steps

### Sau khi setup thành công

1. **Khám phá Dashboard**: Truy cập `http://localhost:3000`
2. **Test API**: Mở `http://localhost:8000/docs` (Swagger UI)
3. **Kiểm tra dữ liệu**: Chạy `python analyze_data.py`
4. **Đọc docs**: Xem `knowledge/` folder
5. **Chạy tests**: `pytest backend/test_main.py -v`

### Tiếp theo

- [ ] Bật `AUTH_REQUIRED=true` cho production
- [ ] Config database PostgreSQL thực tế
- [ ] Cấu hình OpenRouter API key (nếu dùng AI insights)
- [ ] Deploy lên cloud (AWS, GCP, Azure, Vercel)
- [ ] Setup CI/CD pipelines (GitHub Actions)

---

## 📞 Support & Resources

### Liên hệ & Support

- **Issues**: Mở issue trên GitHub
- **Docs**: Xem `knowledge/` folder
- **Questions**: Tạo Discussion trên repo

### Tài Liệu Tham Khảo

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Prophet Documentation](https://facebook.github.io/prophet/)
- [Scikit-learn KMeans](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html)

---

## 📝 License & Version Info

**Project Version**: v2.1.0  
**Last Updated**: 05/04/2026  
**Status**: ✅ Stable & Production Ready

---

**Chúc bạn có trải nghiệm tuyệt vời với AI-Powered Sales Forecasting Dashboard! 🎉**
│   ├── components/
│   │   ├── Dashboard.tsx        ← Main dashboard component
│   │   ├── LoginPage.tsx        ← Login component
│   │   ├── ChartInsightPanel.tsx ← Chart insights
│   │   └── CalendarHeatmap.tsx  ← Heatmap component
│   ├── lib/
│   │   ├── api.ts               ← API client
│   │   ├── auth-api.ts          ← Auth API client
│   │   └── auth-context.tsx     ← Auth context provider
│   ├── public/                  ← Static assets
│   ├── package.json             ← NPM dependencies
│   ├── tsconfig.json            ← TypeScript config
│   ├── next.config.ts           ← Next.js config
│   ├── Dockerfile               ← Docker image
│   └── ESLint configs           ← Code quality
│
├── 📊 data/
│   ├── SampleSuperstore.csv     ← Dataset (9994 records)
│   └── your_final_dataset.csv   ← Processed data
│
├── 🧹 Cleaned_Data/
│   ├── cleaned_sales.csv
│   ├── cleaned_superstore_data.csv
│   ├── category_profit_summary.csv
│   └── top_10_products_by_sales.csv
│
├── 📚 knowledge/
│   ├── README.md                ← Learning resources
│   ├── PRD.md                   ← Product requirements
│   ├── implementation_plan.md   ← Implementation roadmap
│   ├── project_analysis.md      ← Architecture analysis
│   ├── ai-insight-spec.md       ← AI feature specs
│   ├── 01-backend.md            ← Backend guide
│   ├── 02-frontend.md           ← Frontend guide
│   ├── 03-machine-learning.md  ← ML algorithms
│   └── 04-deployment.md         ← Deployment guide
│
└── 🏛️ legacy/
    ├── ai-powered-sales-forecasting-dashboard.ipynb
    └── app.py (v1.0)
```

---

## 🔧 Troubleshooting

### Backend Issues

#### ❌ `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Solution: Cài lại dependencies
cd backend
pip install -r requirements.txt --upgrade
```

#### ❌ `Port 8000 already in use`
```bash
# Solution 1: Tìm process chiếm port
lsof -i :8000          # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Solution 2: Dùng port khác
python -m uvicorn main:app --port 8001
```

#### ❌ `Connection refused (Database)`
```bash
# Solution 1: Kiểm tra PostgreSQL running
# Solution 2: Dùng SQLite (mặc định)
# Solution 3: Config .env với host/port đúng
```

#### ❌ `JWT Secret Key error`
```bash
# Solution: .env phải có SECRET_KEY (min 32 chars)
SECRET_KEY=your-super-secret-key-that-is-long-enough-32-chars
```

### Frontend Issues

#### ❌ `Cannot GET /api/...`
```bash
# Solution 1: Kiểm tra backend chạy (port 8000)
# Solution 2: Kiểm tra NEXT_PUBLIC_API_URL env
# Solution 3: CORS configuration trong backend
```

#### ❌ `npm install fails`
```bash
# Solution 1: Xóa node_modules & package-lock.json
rm -rf node_modules package-lock.json  # macOS/Linux
rmdir /s /q node_modules & del package-lock.json  # Windows

# Solution 2: Cài lại
npm install

# Solution 3: Dùng npm cache clean
npm cache clean --force
npm install
```

#### ❌ `Tailwind CSS not loading`
```bash
# Solution: Build Tailwind
npm run build

# Hoặc dev mode với watch
npm run dev
```

### Docker Issues

#### ❌ `docker-compose command not found`
```bash
# Solution: Cập nhật Docker
docker --version  # Min 24.0
docker-compose --version  # Min 2.0
```

#### ❌ `Container exits immediately`
```bash
# Solution: Xem logs
docker-compose logs backend
docker logs <container_name>
```

---

## 📋 Data Dictionary

### SampleSuperstore.csv

| Column | Type | Range | Mô Tả |
|--------|------|-------|-------|
| `Row ID` | int | 1-9994 | Unique ID |
| `Order ID` | str | - | Order identifier |
| `Order Date` | date | 2014-2017 | Ngày đặt hàng |
| `Ship Date` | date | 2014-2017 | Ngày giao hàng |
| `Ship Mode` | str | Same Day, First Class, Standard | Loại vận chuyển |
| `Customer ID` | str | - | Customer identifier |
| `Customer Name` | str | - | Tên khách hàng |
| `Segment` | str | Consumer, Corporate, Home Office | Phân khúc khách |
| `Country` | str | United States | Quốc gia |
| `City` | str | - | Thành phố |
| `State` | str | - | Bang/Vùng |
| `Postal Code` | int | - | Mã bưu điện |
| `Region` | str | South, East, Central, West | Khu vực |
| `Product ID` | str | - | Product identifier |
| `Category` | str | Furniture, Office Supplies, Technology | Danh mục |
| `Sub-Category` | str | 17 values | Danh mục con |
| `Product Name` | str | - | Tên sản phẩm |
| `Sales` | float | 0.44 - 22638.48 | Doanh số bán hàng |
| `Quantity` | int | 1-14 | Số lượng |
| `Discount` | float | 0.0 - 0.2 | Chiết khấu (0-20%) |
| `Profit` | float | -6626 - 8399.98 | Lợi nhuận |

---

## 🚀 Next Steps

### Sau khi setup thành công

1. **Khám phá Dashboard**: Truy cập `http://localhost:3000`
2. **Test API**: Mở `http://localhost:8000/docs` (Swagger UI)
3. **Kiểm tra dữ liệu**: Chạy `python analyze_data.py`
4. **Đọc docs**: Xem `knowledge/` folder
5. **Chạy tests**: `pytest backend/test_main.py -v`

### Tiếp theo

- [ ] Bật `AUTH_REQUIRED=true` cho production
- [ ] Config database PostgreSQL thực tế
- [ ] Cấu hình OpenRouter API key (nếu dùng AI insights)
- [ ] Deploy lên cloud (AWS, GCP, Azure, Vercel)
- [ ] Setup CI/CD pipelines (GitHub Actions)
