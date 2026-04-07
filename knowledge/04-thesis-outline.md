# 📚 Bài Tiểu Luận: Phần 4.4 - Kiến Trúc Tích Hợp API & JWT Authentication

## ✍️ OUTLINE CHO TIỂU LUẬN (Dùng để viết)

---

## **I. GIỚI THIỆU (Introduction) — ~300 từ**

### Vấn Đề Đặt Ra
- Hệ thống bán hàng hiện đại cần bảo vệ dữ liệu nhạy cảm (doanh thu, khách hàng)
- Không thể để API public mà không kiểm tra quyền hạn
- Cần giải pháp authentication & authorization vừa bảo mật vừa dễ scale

### Giải Pháp Đề Xuất
Dự án sử dụng **JWT (JSON Web Token)** kết hợp **RBAC (Role-Based Access Control)** để:
- ✅ Xác thực người dùng an toàn
- ✅ Phân quyền dựa trên vai trò (roles)
- ✅ Bảo vệ các endpoint API  
- ✅ Không cần session storage

---

## **II. KIẾN TRÚC TỔNG QUAN (Architecture Overview) — ~400 từ**

### 2.1 Request Flow Diagram

```
┌─────────────┐
│   Client    │ Browser/Mobile
└──────┬──────┘
       │ 1. POST /auth/login
       │    {username, password}
       ↓
┌─────────────────────┐
│  Backend (FastAPI)  │
│                     │
│ [Authentication]    │ 2. Verify credentials
│ 3. Return JWT       │
└──────┬──────────────┘
       │ Token: eyJhbGc...
       ↓
┌─────────────┐
│   Client    │ Save in localStorage
└──────┬──────┘
       │ 4. GET /api/kpis
       │    Header: Authorization: Bearer eyJhbGc...
       ↓
┌─────────────────────┐
│  Backend (FastAPI)  │
│                     │
│ [Verify JWT]        │ 5. Decode & validate
│ [Check Role]        │
│ [Process Request]   │ 6. Return data
└──────┬──────────────┘
       │ {kpis: {...}}
       ↓
┌─────────────┐
│   Client    │ Render dashboard
└─────────────┘
```

### 2.2 Ba Cụm API Chính (API Clusters)

```
📌 PUBLIC ENDPOINTS (Không cần token)
├─ GET  /              Welcome message
├─ GET  /health        System health check
└─ POST /auth/login    Login (trả JWT)

🔐 AUTHENTICATION ENDPOINTS (Luôn hoạt động)
├─ POST /auth/login           Đăng nhập
├─ POST /auth/signup          Đăng ký (role=viewer)
├─ POST /auth/register        Tạo user (admin only)
├─ GET  /auth/me              Thông tin user
├─ GET  /auth/users           Danh sách users (admin)
├─ PUT  /auth/change-password Đổi mật khẩu
├─ DELETE /auth/users/{id}    Xóa user (admin)
└─ POST /auth/logout          Đăng xuất

📊 DATA ENDPOINTS (Protected khi AUTH_REQUIRED=true)
├─ GET /api/filters
├─ GET /api/kpis
├─ GET /api/charts/sales-trend
├─ GET /api/charts/category-sales
├─ GET /api/forecast
├─ GET /api/customer-segmentation
├─ GET /api/sales-heatmap
├─ POST /api/ai/insights
└─ GET /api/ai/insights/{id}
```

---

## **III. JWT (JSON Web Token) CỤ THỂ — ~600 từ**

### 3.1 JWT Là Gì?

JWT là một chuỗi được mã hóa chứa 3 phần ngăn cách bởi dấu chấm (`.`):

```
Header.Payload.Signature
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcwMzAwMDAwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Phần 1: Header** (Mã hóa Base64)
```json
{
  "alg": "HS256",  // Algorithm: HMAC SHA-256
  "typ": "JWT"     // Type
}
```

**Phần 2: Payload** (Mã hóa Base64) — thông tin user
```json
{
  "sub": "admin",        // Subject (username)
  "role": "admin",       // User's role
  "exp": 1703000000      // Expiration timestamp (Unix)
}
```

**Phần 3: Signature** — kiểm tra tính toàn vẹn
```
HMACSHA256 = HMAC-SHA256(
  (Header + Payload).encode(),
  SECRET_KEY = "secret-key-from-env"
)
```

### 3.2 Cài Đặt Trong Dự Án

**3.2.1 Tạo Token** ([`backend/auth.py` line 92-98](backend/auth.py#L92-L98)):
```python
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "default-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token with expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**3.2.2 Validate Token** ([`backend/auth.py` line 100-110](backend/auth.py#L100-L110)):
```python
from jose import JWTError

def decode_token(token: str) -> Optional[TokenData]:
    """Decode & validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        return TokenData(username=username, role=role)
    except JWTError:  # Token hết hạn hoặc signature sai
        return None
```

### 3.3 Login Endpoint

**Sơ đồ logic**:
```
1. Client gửi {username, password}
   ↓
2. Verify credentials vs. database
   ↓
3. Nếu đúng: tạo JWT token
   ↓
4. Return token + expiration time
   ↓
5. Client lưu token vào localStorage
```

**Thực thi ([`backend/main.py` line 251-272](backend/main.py#L251-L272))**:
```python
@app.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")  # Rate limiting: max 10 requests/minute
def login(request: Request, user_data: UserLogin):
    # Step 1: Verify password
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        logger.warning(f"Failed login: {user_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Step 2: Create JWT token
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    
    # Step 3: Return
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=60 * 60  # seconds
    )
```

### 3.4 Frontend Integration

**Lưu token** ([`frontend/lib/auth-context.tsx`](frontend/lib/auth-context.tsx)):
```typescript
const response = await fetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({username, password})
});
const {access_token} = await response.json();
localStorage.setItem('auth_token', access_token);  // ← Lưu
```

**Attach token vào request** ([`frontend/lib/api.ts` line 7-16](frontend/lib/api.ts#L7-L16)):
```typescript
const api = axios.create({baseURL: 'http://localhost:8000/api'});

// Interceptor: thêm token vào mọi request
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;  // ← Thêm Header
    }
    return config;
});
```

---

## **IV. ROLE-BASED ACCESS CONTROL (RBAC) — ~500 từ**

### 4.1 Ba Cấp Độ Quyền Hạn (Roles)

| Role | API Read | API Write | User Mgmt | Ví Dụ |
|------|----------|-----------|----------|--------|
| **viewer** | ✅ Dashboard, KPI, Chart | ❌ | ❌ | Marketing staff |
| **editor** | ✅ | ✅ Config, Settings | ❌ | Senior analyst |
| **admin** | ✅ | ✅ | ✅ Manage users | System admin |

**1 người dùng = 1 role (không multiple roles)**

### 4.2 Cài Đặt Roles Trong Code

**Định nghĩa** ([`backend/auth.py` line 30-34](backend/auth.py#L30-L34)):
```python
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "viewer"  # Mặc định là viewer

# Validation
def register_user(username: str, password: str, role: str = "viewer") -> dict:
    if role not in ("viewer", "editor", "admin"):
        raise ValueError("Role must be one of: viewer, editor, admin")
    ...
```

### 4.3 Kiểm Soát Quyền Hạn

**Wrapper function `require_admin()`** ([`backend/auth.py` line 148-156](backend/auth.py#L148-L156)):
```python
from fastapi import Depends, HTTPException, status

async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: lọc chỉ cho admin"""
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

**Dùng trong endpoint** ([`backend/main.py` line 305-311](backend/main.py#L305-L311)):
```python
@app.get("/auth/users")
def list_users(admin: dict = Depends(require_admin)):  # ← Bắt buộc admin
    """Chỉ admin mới thấy danh sách users"""
    return [
        {"username": u["username"], "role": u["role"]}
        for u in users_db.values()
    ]
```

### 4.4 Dependency Injection Pattern

FastAPI dùng **dependency injection** để verify role:

```
Endpoint được gọi
    ↓
FastAPI check `Depends(require_admin)`
    ↓
    Gọi `get_current_user(token)`
        ↓
        Decode JWT token
        ↓
        Kiểm tra user tồn tại
        ↓
        Return user dict
    ↓
    Gọi `require_admin(current_user)`
        ↓
        Check current_user.role == "admin"?
        ↓
        Nếu không → raise 403 Forbidden
        ↓
        Nếu có → continue
    ↓
Endpoint logic được chạy
```

---

## **V. BẢO MẬT (Security Measures) — ~400 từ**

### 5.1 Password Hashing

❌ **Sai (nguy hiểm!):**
```python
users_db[username] = password  # Lưu plaintext!
```

✅ **Đúng:**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Lưu hash
hashed_password = pwd_context.hash(password)
users_db[username] = hashed_password

# Verify
is_correct = pwd_context.verify(password, hashed_password)
```

**Cài đặt dự án** ([`backend/auth.py` line 82-88](backend/auth.py#L82-L88)):
```python
def hash_password(password: str) -> str:
    return pwd_context.hash(password)  # bcrypt with salt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### 5.2 Rate Limiting

Ngăn brute-force attack (thử password nhiều lần):

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("10/minute")  # Max 10 login attempts per minute
def login(...):
    ...

@app.post("/auth/register")
@limiter.limit("5/minute")   # Max 5 signups per minute
def signup(...):
    ...
```

### 5.3 Token Expiration

Token expire tự động sau 60 phút:

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})  # ← Expiration
    return jwt.encode(...)
```

**Khi decode, nếu `exp` < now → token hết hạn:**
```python
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # ← Nếu token hết hạn, jwt.decode sẽ raise JWTError
    except JWTError:
        return None
```

### 5.4 CORS (Cross-Origin Resource Sharing)

Chỉ cho phép frontend từ domain cụ thể:

```python
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ← Whitelist
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### 5.5 Request Logging

Log mọi request để audit & debug

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time}ms "
        f"- IP: {request.client.host}"
    )
    return response
```

---

## **VI. CẤU HÌNH & BIẾN MÔI TRƯỜNG — ~250 từ**

### 6.1 `.env` Configuration

```env
# ─── Authentication ─────────────────────
AUTH_REQUIRED=false                      # true: require JWT for all /api/*
SECRET_KEY=your-strong-secret-key        # MUST change in production
TOKEN_EXPIRE_MINUTES=60                  # JWT expiration time

# ─── Rate Limiting ──────────────────────
RATE_LIMIT=100/minute                    # Global rate limit

# ─── CORS ───────────────────────────────
ALLOWED_ORIGINS=http://localhost:3000    # Frontend URL
```

### 6.2 Environment Types

| Var | Value | Behavior |
|-----|-------|----------|
| `AUTH_REQUIRED` | `false` | Dev mode: API public, no token needed |
| `AUTH_REQUIRED` | `true` | Prod mode: All `/api/*` return 401 without token |
| `SECRET_KEY` | `$RANDOM_STRING` | Use strong 32+ character key |

---

## **VII. TESTING & VERIFICATION — ~250 từ**

### 7.1 Unit Tests (Test Auth Endpoints)

```bash
# Cài pytest
pip install pytest

# Run tests
cd backend
pytest -v test_main.py::TestAuthEndpoints
```

**Test cases** ([`backend/test_main.py` line 113-240](backend/test_main.py#L113-L240)):

1. ✅ `test_login_success` - Đăng nhập đúng → return JWT
2. ✅ `test_login_wrong_password` - Sai password → 401
3. ✅ `test_signup_creates_viewer` - Signup → role = viewer
4. ✅ `test_register_admin_only` - Register user (admin only)
5. ✅ `test_list_users_non_admin` - Non-admin → 403
6. ✅ `test_invalid_token` - Token giả → 401
7. ✅ `test_role_authorization` - Role check works

### 7.2 Manual Testing

```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn main:app --reload

# Terminal 2: Test API
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Response:
# {"access_token":"eyJhbGc...","token_type":"bearer","expires_in":3600}

# 2. Use token
curl http://localhost:8000/api/kpis \
  -H "Authorization: Bearer eyJhbGc..."

# 3. Test rate limit (try 11 times quickly)
for i in {1..11}; do
  curl -X POST http://localhost:8000/auth/login \
    -d '{"username":"admin","password":"admin123"}'
done
# 11th request → 429 Too Many Requests
```

---

## **VIII. GIỚI HẠN & CẢI THIỆN TƯƠNG LAI — ~300 từ**

### 8.1 Hiện Tại (Current Limitations)

| Vấn Đề | Tác Động | Giải Pháp |
|--------|---------|----------|
| Users lưu in-memory | Mất dữ liệu khi restart | Dùng PostgreSQL |
| Chỉ có access token | Token không refresh | Thêm refresh token endpoint |
| Không invalidate token | Logout không hiệu quả | Dùng Redis blacklist |
| Editor role không dùng | Chưa có permission check | Implement `require_editor()` |

### 8.2 Future Roadmap

**Phase 1: Persistence** (1 tuần)
- Migrate users từ dict → PostgreSQL
- Setup migration scripts

**Phase 2: Token Refresh** (3 ngày)
- Implement refresh token mechanism
- Return {access_token, refresh_token}

**Phase 3: Logout Handling** (2 ngày)
- Setup Redis
- Token blacklist on logout

**Phase 4: Permission Granularity** (1 tuần)
- Editor role endpoints
- Fine-grained permissions per API

---

## **IX. KẾT LUẬN — ~200 từ**

### Tóm Lại
Dự án sử dụng **JWT + RBAC** là một giải pháp hiện đại, bảo mật, dễ scale cho API authentication. Các đặc tính chính:

✅ **Token-based**: Không cần session storage, dễ scale horizontal (microservices)
✅ **Stateless**: Server không cần nhớ client, just verify signature  
✅ **Role-based**: 3 levels (viewer/editor/admin), dependency injection pattern
✅ **Secure**: bcrypt, rate limiting, CORS, token expiration

### Điểm Mạnh
- Compliance với OAuth2 standard
- Frontend integration straightforward (localStorage + interceptor)
- Test coverage comprehensive
- Production-ready code (tính toàn bộ)

### Điểm Yếu
- In-memory storage (dev only, cần migrate to DB)
- No refresh mechanism (UX issues)
- No token invalidation (logout không hoàn chỉnh)

### Hướng Phát Triển
Sau khi hoàn thiện những limitation trên, hệ thống sẽ đạt mức **production-ready** và có thể scale support:
- Đa ngành hàng, multi-tenant
- Microservices architecture  
- Distributed caching (Redis)
- Advanced audit logging

---

## **THAM KHẢO (References)**

```
[1] JWT (RFC 7519): https://tools.ietf.org/html/rfc7519
[2] OAuth 2.0 Bearer Token: https://tools.ietf.org/html/rfc6750
[3] OWASP: Authentication Cheat Sheet
[4] FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
[5] Passlib Documentation: https://passlib.readthedocs.io/
[6] Rate Limiting Best Practices: https://slowapi.readthedocs.io/
```

---

## **PHỤ LỤC A: CODE SNIPPET COMPLETˌ**

Để dễ tham khảo khi viết tiểu luận, tất cả code snippets đã được link tới file gốc trong dự án.

Ví dụ:
- [`backend/auth.py`](backend/auth.py) — JWT implementation
- [`backend/main.py`](backend/main.py#L251) — Login endpoint
- [`frontend/lib/api.ts`](frontend/lib/api.ts) — Token management

---

**Created**: 2026-04-06  
**For**: Tiểu Luận Phần 4.4 - Kiến Trúc Tích Hợp API và JWT Authentication  
**Status**: Ready for thesis writing
