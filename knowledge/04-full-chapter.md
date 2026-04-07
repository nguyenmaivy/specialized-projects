# 4.4. Kiến Trúc Tích Hợp API và Bảo Mật (JWT Authentication)

## Tóm Tắt Nội Dung
Chương này trình bày kiến trúc bảo mật hệ thống sử dụng JSON Web Token (JWT) và Role-Based Access Control (RBAC) để xác thực người dùng và phân quyền truy cập các endpoint API. Hệ thống được thiết kế với ba lớp bảo mật: public endpoints, authentication endpoints, và protected data endpoints.

---

## 1. Giới Thiệu

### 1.1 Vấn Đề Đặt Ra
Dalam một hệ thống quản lý bán hàng hiện đại, dữ liệu kinh doanh như doanh thu, lợi nhuận, thông tin khách hàng cần được bảo vệ khỏi truy cập trái phép. Các API công khai mà không có cơ chế xác thực sẽ:
- ❌ Cho phép bất kỳ ai truy cập dữ liệu nhạy cảm
- ❌ Không theo dõi được ai đã truy cập hệ thống
- ❌ Không thể phân quyền dựa trên vai trò người dùng
- ❌ Vi phạm các tiêu chuẩn bảo mật OWASP

### 1.2 Giải Pháp Được Chọn
Dự án sử dụng **JWT (JSON Web Token)** kết hợp **RBAC (Role-Based Access Control)** để:

✅ **Xác thực an toàn**: Mỗi request phải có token hợp lệ  
✅ **Phân quyền linh hoạt**: 3 cấp độ role (viewer, editor, admin)  
✅ **Scalable**: Stateless token design, không cần session storage  
✅ **Tuân chuẩn**: Comply với OAuth 2.0 Bearer Token (RFC 6750)

---

## 2. Kiến Trúc Tổng Quan

### 2.1 Request Flow Diagram

Hình 4.4.1 minh họa luồng request từ client đến server:

```flow
┌──────────────────────────────────────────────────────────────┐
│ STEP 1: LOGIN FLOW                                           │
│ ┌─────────────┐                                              │
│ │   CLIENT    │─────────────────────────────────┐            │
│ └─────────────┘ POST /auth/login                │            │
│                 {username: "admin",             │            │
│                  password: "admin123"}          │            │
│                                                  │            │
│                                            ┌────▼────────────┤
│                                            │  BACKEND         │
│                                            │ ┌──────────────┐ │
│                                            │ │ 1. Verify    │ │
│                                            │ │    password  │ │
│                                            │ └──────────────┘ │
│                                            │ ┌──────────────┐ │
│                                            │ │ 2. Get user  │ │
│                                            │ │    role      │ │
│                                            │ └──────────────┘ │
│                                            │ ┌──────────────┐ │
│                                            │ │ 3. Create    │ │
│                                            │ │    JWT token │ │
│                                            │ └──────────────┘ │
│                                            └────┬─────────────┤
│                                                 │              │
│                 {access_token: "eyJhbGc...",   │              │
│                  token_type: "bearer",         │              │
│                  expires_in: 3600}             │              │
│ ┌──────────────┐◄────────────────────────────┘              │
│ │   CLIENT     │ Save to localStorage                        │
│ └──────────────┘                                             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ STEP 2: API REQUEST WITH AUTHENTICATION                      │
│ ┌─────────────┐                                              │
│ │   CLIENT    │─────────────────────────────────┐            │
│ └─────────────┘ GET /api/kpis                   │            │
│                 Header: Authorization:         │            │
│                 Bearer eyJhbGc...              │            │
│                                                  │            │
│                                            ┌────▼────────────┤
│                                            │  BACKEND         │
│                                            │ ┌──────────────┐ │
│                                            │ │ 1. Extract   │ │
│                                            │ │    token     │ │
│                                            │ └──────────────┘ │
│                                            │ ┌──────────────┐ │
│                                            │ │ 2. Verify    │ │
│                                            │ │    signature │ │
│                                            │ └──────────────┘ │
│                                            │ ┌──────────────┐ │
│                                            │ │ 3. Check     │ │
│                                            │ │    expiration│ │
│                                            │ └──────────────┘ │
│                                            │ ┌──────────────┐ │
│                                            │ │ 4. Verify    │ │
│                                            │ │    user role │ │
│                                            │ └──────────────┘ │
│                                            │ ┌──────────────┐ │
│                                            │ │ 5. Process   │ │
│                                            │ │    request   │ │
│                                            │ └──────────────┘ │
│                                            └────┬─────────────┤
│                                                 │              │
│                 {total_sales: 150000,          │              │
│                  total_profit: 28000,         │              │
│                  ...}                         │              │
│ ┌──────────────┐◄────────────────────────────┘              │
│ │   CLIENT     │ Render dashboard                            │
│ └──────────────┘                                             │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Ba Cụm API Chính

Hệ thống API được chia thành ba nhóm theo mức độ bảo mật:

**📌 PUBLIC ENDPOINTS** (Không yêu cầu token)
```
GET  /              Welcome message
GET  /health        Health check (server monitoring)
```

**🔐 AUTHENTICATION ENDPOINTS** (Luôn hoạt động, quản lý vòng đời user)
```
POST /auth/login              Đăng nhập, trả JWT token
POST /auth/signup             Đăng ký public (gán role=viewer)
POST /auth/register           Tạo user mới (admin only)
GET  /auth/me                 Lấy thông tin user hiện tại
GET  /auth/users              Danh sách tất cả users (admin only)
PUT  /auth/change-password    Đổi mật khẩu
DELETE /auth/users/{username} Xóa user (admin only)
POST /auth/logout             Đăng xuất
```

**📊 DATA ENDPOINTS** (Protected, phụ thuộc AUTH_REQUIRED)
```
GET /api/filters                Tùy chọn bộ lọc
GET /api/kpis                   Key Performance Indicators
GET /api/charts/sales-trend     Xu hướng bán hàng
GET /api/charts/category-sales  Doanh thu theo category
GET /api/charts/region-sales    Doanh thu theo region
GET /api/forecast               Dự báo 30 ngày
GET /api/customer-segmentation  Phân khúc khách hàng (RFM)
GET /api/sales-heatmap          Heatmap lịch doanh thu
POST /api/ai/insights           Tạo AI insights
GET /api/ai/insights/{id}       Lấy AI insights
```

---

## 3. JWT (JSON Web Token) - Chi Tiết Cài Đặt

### 3.1 JWT Là Gì?

JWT (RFC 7519) là một chuỗi mã hóa gồm ba phần ngăn cách bởi dấu chấm (`.`):

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcwMzAwMDAwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
│ HEADER │││ PAYLOAD │││ SIGNATURE │
```

**Tảng 1: Header** (Base64 encoded)
```json
{
  "alg": "HS256",    // Algorithm: HMAC SHA-256
  "typ": "JWT"       // Type
}
```

**Phần 2: Payload** (Base64 encoded) - chứa thông tin user
```json
{
  "sub": "admin",        // Subject (username)
  "role": "admin",       // User's role
  "exp": 1703000000      // Expiration timestamp (Unix epoch)
}
```

**Phần 3: Signature** - đảm bảo tính toàn vẹn
```
HMACSHA256(
  base64_encode(HEADER) + "." + base64_encode(PAYLOAD),
  SECRET_KEY
)
```

Bất kỳ thay đổi nào trong header hoặc payload sẽ làm signature không khớp, token bị từ chối.

### 3.2 Tạo Token (Create)

Khi người dùng đăng nhập thành công, server tạo JWT token:

```python
# backend/auth.py - lines 92-98
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "default-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**Logic**:
1. Copy dữ liệu user (username, role)
2. Thêm expiration time (hiện tại + 60 phút)
3. Encode với SECRET_KEY bằng HS256
4. Return token string

### 3.3 Validate Token (Decode)

Khi client gửi request kèm token, server phải validate:

```python
# backend/auth.py - lines 100-110
from jose import JWTError

def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            return None
        return TokenData(username=username, role=role)
    except JWTError:  # Token hết hạn HOẶC signature sai
        return None
```

**Logic**:
1. Decode token bằng SECRET_KEY
2. Nếu token hết hạn → JWTError → return None
3. Nếu signature sai → JWTError → return None
4. Nếu hợp lệ → extract username & role

### 3.4 Login Endpoint

Endpoint `/auth/login` là điểm vào để lấy token:

```python
# backend/main.py - lines 251-272
@app.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")  # Rate limiting: max 10 login/minute
def login(request: Request, user_data: UserLogin):
    """Authenticate user and return JWT token"""
    # Step 1: Verify credentials
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {user_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Step 2: Create JWT token
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    
    # Step 3: Return token response
    logger.info(f"User logged in: {user['username']}")
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=int(os.getenv("TOKEN_EXPIRE_MINUTES", "60")) * 60
    )
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 3600
# }
```

### 3.5 Frontend Token Management

Frontend lưu token và attach vào mọi request:

```typescript
// frontend/lib/api.ts - lines 7-16
const api = axios.create({
    baseURL: 'http://localhost:8000/api',
});

// Interceptor: tự động thêm token vào Authorization header
api.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined' 
        ? localStorage.getItem('auth_token') 
        : null;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;  // ← Header đúng chuẩn
    }
    return config;
});

// Nếu API trả 401, logout tự động
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            window.location.reload();  // Redirect to login page
        }
        return Promise.reject(error);
    }
);
```

---

## 4. Role-Based Access Control (RBAC)

### 4.1 Ba Cấp Độ Quyền Hạn

| Role | API Read | API Write | User Management | Ví Dụ |
|------|----------|-----------|-----------------|--------|
| **viewer** | ✅ Dashboard, KPI, Chart | ❌ | ❌ | Marketing staff |
| **editor** | ✅ | ✅ Config, Settings | ❌ | Senior analyst |
| **admin** | ✅ | ✅ | ✅ Tạo/xóa user | System admin, CTO |

Mỗi người dùng chỉ có một role duy nhất. Role được xác định khi tạo account và chỉ admin mới có quyền thay đổi.

### 4.2 Định Nghĩa Roles

```python
# backend/auth.py - lines 30-34
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"  # Default: viewer
    
def register_user(username: str, password: str, role: str = "viewer") -> dict:
    """Register a new user with validation"""
    if role not in ("viewer", "editor", "admin"):
        raise ValueError("Role must be one of: viewer, editor, admin")
    
    users_db[username] = {
        "username": username,
        "hashed_password": hash_password(password),
        "role": role
    }
    logger.info(f"User registered: {username} (role: {role})")
    return {"username": username, "role": role}
```

### 4.3 Kiểm Soát Quyền Hạn với Dependency Injection

FastAPI sử dụng **dependency injection** pattern để kiểm soát quyền:

```python
# backend/auth.py - lines 148-156
from fastapi import Depends, HTTPException, status

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: only allow admin role"""
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

**Áp dụng vào endpoint**:

```python
# backend/main.py - lines 305-311
@app.get("/auth/users")
def list_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)"""
    return [
        {"username": u["username"], "role": u["role"]}
        for u in users_db.values()
    ]

@app.delete("/auth/users/{username}")
def delete_user(username: str, admin: dict = Depends(require_admin)):
    """Delete a user (admin only)"""
    try:
        result = delete_user_from_db(username)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Flow**:
```
Client gọi GET /auth/users
        ↓
FastAPI kiểm tra Depends(require_admin)
        ↓
Gọi get_current_user() → decode JWT token
        ↓
Gọi require_admin() → check if role == "admin"
        ↓
Nếu không phải admin → 403 Forbidden
        ↓
Nếu là admin → endpoint logic được chạy
```

### 4.4 Signup vs Register Endpoints

- **POST /auth/signup** (public): Bất kỳ ai cũng đăng ký được, role tự động = "viewer"
  ```python
  @app.post("/auth/signup", response_model=UserResponse)
  def signup(request: Request, user_data: UserCreate):
      # Force role to viewer for public signups
      result = register_user(user_data.username, user_data.password, "viewer")
      return UserResponse(**result)
  ```

- **POST /auth/register** (admin only): Admin tạo user với role cụ thể
  ```python
  @app.post("/auth/register", response_model=UserResponse)
  def register(request: Request, user_data: UserCreate, 
               admin: dict = Depends(require_admin)):
      # Admin can specify role
      result = register_user(user_data.username, user_data.password, user_data.role)
      return UserResponse(**result)
  ```

---

## 5. Bảo Mật (Security Measures)

### 5.1 Password Hashing

Mật khẩu không bao giờ được lưu plaintext. Dự án dùng **bcrypt** with salt:

```python
# backend/auth.py - lines 82-88
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

**Lợi ích**:
- ✅ Ngay cả database bị leak, hacker không thể đoán password
- ✅ Bcrypt có "salt", mỗi hash khác nhau dù password giống
- ✅ Khó tính toán ngược (cost factor = 12 mặc định)

### 5.2 Rate Limiting

Ngăn brute-force attack (thử password nhiều lần):

```python
# backend/main.py - lines 251, 274, 285
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("10/minute")  # Max 10 login attempts/minute
def login(...):
    ...

@app.post("/auth/register")
@limiter.limit("5/minute")   # Max 5 registrations/minute
def register(...):
    ...

@app.post("/auth/signup")
@limiter.limit("5/minute")   # Max 5 public signups/minute
def signup(...):
    ...
```

Nếu vượt limit, trả về **HTTP 429 Too Many Requests**.

### 5.3 Token Expiration

Token tự động expire sau 60 phút (configurable):

```python
# backend/auth.py - line 20
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "60"))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})  # ← Expiration claim
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # ← Nếu token hết hạn, jwt.decode() tự động raise JWTError
    except JWTError:
        return None  # Token invalid hoặc expired
```

### 5.4 CORS (Cross-Origin Resource Sharing)

Chỉ cho phép frontend từ domain được whitelist:

```python
# backend/main.py - lines 159-169
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,        # Whitelist
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

Nếu frontend từ domain không được whitelist → CORS error trên browser.

### 5.5 Request Logging

Mọi request được log để audit & debug:

```python
# backend/main.py - lines 172-184
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every HTTP request with method, path, status, time"""
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
```

**Log output ví dụ**:
```
2026-04-06 10:23:45 - POST /auth/login - Status: 200 - Time: 45.32ms - IP: 127.0.0.1
2026-04-06 10:23:46 - GET /api/kpis - Status: 200 - Time: 120.15ms - IP: 127.0.0.1
2026-04-06 10:23:47 - GET /auth/users - Status: 403 - Time: 2.10ms - IP: 127.0.0.1
```

---

## 6. Cấu Hình Biến Môi Trường

### 6.1 Environment Variables

```env
# .env file
# ─── Authentication ─────────────────────
AUTH_REQUIRED=false                          # true: bắt buộc JWT
SECRET_KEY=your-strong-secret-key-32-chars   # MUST change in production
TOKEN_EXPIRE_MINUTES=60                      # Token lifetime

# ─── Rate Limiting ──────────────────────
RATE_LIMIT=100/minute                        # Global API rate limit

# ─── CORS ───────────────────────────────
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### 6.2 Hai Chế Độ Vận Hành

| Mode | `AUTH_REQUIRED` | Hành Vi | Dùng Cho |
|------|----|---------|---------|
| **Development** | `false` | API public, không cần token, vẫn có auth endpoints | Testing, demo nội bộ |
| **Production** | `true` | All `/api/*` trả 401 nếu không có token | Production deployment |

---

## 7. Testing & Verification

### 7.1 Unit Tests

Dự án có test suite comprehensive với 90+ test cases:

```bash
# Run authentication tests
cd backend
pytest -v test_main.py::TestAuthEndpoints
```

**Test cases** (từ `backend/test_main.py`):

1. ✅ `test_login_success` - Login đúng → return JWT
2. ✅ `test_login_wrong_password` - Sai password → 401
3. ✅ `test_login_nonexistent_user` - User không tồn tại → 401
4. ✅ `test_signup_creates_viewer` - Signup → role = viewer
5. ✅ `test_register_admin_only` - Register user (admin only)
6. ✅ `test_list_users_admin` - Admin view all users
7. ✅ `test_list_users_non_admin` - Non-admin → 403
8. ✅ `test_invalid_token` - Token giả → 401
9. ✅ `test_expired_token_format` - Token malformed → 401
10. ✅ `test_rate_limit` - Vượt limit → 429

### 7.2 Manual Testing

**Bước 1: Start backend**
```bash
cd backend
python -m uvicorn main:app --reload
```

**Bước 2: Test login**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcwMzAwMDAwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
#   "token_type": "bearer",
#   "expires_in": 3600
# }
```

**Bước 3: Dùng token để gọi protected API**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl http://localhost:8000/api/kpis \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "total_sales": 150000,
#   "total_profit": 28000,
#   "total_orders": 500,
#   "avg_discount": 0.15
# }
```

**Bước 4: Test rate limiting**
```bash
# Try 11 login requests quickly (limit = 10/minute)
for i in {1..11}; do
  curl -X POST http://localhost:8000/auth/login \
    -d '{"username":"admin","password":"admin123"}'
done

# 11th request -> 429 Too Many Requests
```

---

## 8. Giới Hạn Hiện Tại & Cải Thiện Tương Lai

### 8.1 Những Vấn Đề Cần Cải Thiện

| Vấn Đề | Tác Động | Giải Pháp |
|--------|---------|----------|
| **In-memory users storage** | Mất dữ liệu khi server restart | Migrate to PostgreSQL |
| **Chỉ có access token** | Token không refresh, logout UX tệ | Implement refresh token |
| **Token không invalidate** | Logout không hiệu quả | Dùng Redis blacklist |
| **Editor role placeholder** | Không có permission check | Implement `require_editor()` |
| **No password reset** | Quên mật khẩu không thể update | Admin reset endpoint |

### 8.2 Roadmap Cải Thiện

**Phase 1: Database Persistence** (Ưu tiên cao)
- Migrate users từ dictionary → PostgreSQL table
- Setup SQLAlchemy ORM models
- Write migration scripts

**Phase 2: Refresh Token Mechanism** (Ưu tiên trung bình)
- Return {access_token, refresh_token} khi login
- Implement `/auth/refresh` endpoint
- Refresh token expire 7 ngày, access token 1 giờ

**Phase 3: Token Blacklist** (Ưu tiên trung bình)
- Setup Redis instance
- Add token to blacklist khi logout
- Check blacklist khi validate token

**Phase 4: Permission Granularity** (Ưu tiên thấp)
- Create `require_editor()` dependency
- Implement per-API permission checks
- Setup role migration path (viewer → editor → admin)

---

## 9. Kết Luận

### 9.1 Tóm Lại

Hệ thống sử dụng **JWT + RBAC** là một giải pháp hiện đại, bảo mật, và dễ mở rộng cho API authentication. Các đặc điểm chính:

✅ **Token-based**: Không cần session storage, dễ scale horizontal (microservices)  
✅ **Stateless**: Server không cần nhớ client state, chỉ verify signature  
✅ **Role-based**: 3 levels (viewer/editor/admin), flexible permission model  
✅ **Secure**: bcrypt password hashing, rate limiting, CORS, token expiration  
✅ **Standard**: Comply với OAuth 2.0 (RFC 6750) & JWT (RFC 7519)

### 9.2 Điểm Mạnh

- 🟢 Implementation đúng chuẩn OAuth2 standard
- 🟢 Frontend integration straightforward (localStorage + axios interceptor)
- 🟢 Comprehensive test coverage (90+ test cases)
- 🟢 Production-ready code architecture
- 🟢 Configurable via environment variables

### 9.3 Điểm Yếu (Development-mode limitations)

- 🟠 In-memory user storage (dev only, cần migrate to database)
- 🟠 No refresh token mechanism (token expire sau 1 giờ)
- 🟠 Token không invalidate khi logout (session không track)
- 🟠 Editor role defined nhưng không implement fully

### 9.4 Hướng Phát Triển

Sau khi hoàn thiện những limitation trên, hệ thống sẽ đạt mức **production-ready** và có thể scale support:
- 🚀 Multi-tenant architecture
- 🚀 Microservices deployment
- 🚀 Distributed caching (Redis)
- 🚀 Advanced audit logging
- 🚀 Single Sign-On (SSO) integration

### 9.5 Đánh Giá Chung

| Tiêu Chí | Điểm | Ghi Chú |
|---------|------|--------|
| JWT Implementation | 8/10 | Chuẩn OAuth2, cần refresh token |
| RBAC Design | 7/10 | 3 roles ok, editor chưa implement |
| Security Measures | 8/10 | Bcrypt, rate limiting, CORS ✅ |
| Production Readiness | 6/10 | In-memory storage là vấn đề lớn |
| Testing | 9/10 | Comprehensive test suite |
| Frontend Integration | 8/10 | Axios interceptor clean |
| **Overall** | **7.5/10** | **Development-ready, needs DB persistence** |

---

## Tham Khảo

```
[1] RFC 7519 - JSON Web Token (JWT)
    https://tools.ietf.org/html/rfc7519

[2] RFC 6750 - OAuth 2.0 Bearer Token Usage
    https://tools.ietf.org/html/rfc6750

[3] OWASP - Authentication Cheat Sheet
    https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet

[4] FastAPI - Security Documentation
    https://fastapi.tiangolo.com/tutorial/security/

[5] Passlib - Password Hashing Documentation
    https://passlib.readthedocs.io/

[6] slowapi - Rate Limiting Library
    https://slowapi.readthedocs.io/

[7] python-jose - JWT Implementation
    https://python-jose.readthedocs.io/
```

---

**Chương 4.4 - Kiến Trúc Tích Hợp API và Bảo Mật (JWT Authentication)**  
*Dự Án: AI-Powered Sales Forecasting Dashboard*  
*Ngày: 06/04/2026*  
*Trạng Thái: Hoàn thành*
