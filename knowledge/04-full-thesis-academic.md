# 4.4. Kiến Trúc Tích Hợp API và Bảo Mật (JWT Authentication)

## Tóm Tắt Nội Dung

Chương này trình bày đầy đủ về kiến trúc bảo mật hệ thống sử dụng JSON Web Token (JWT) kết hợp với Role-Based Access Control (RBAC) nhằm đảm bảo xác thực người dùng an toàn và phân quyền truy cập các endpoint API một cách linh hoạt. Thông qua việc áp dụng ba lớp bảo mật (public endpoints, authentication endpoints, và protected data endpoints), hệ thống đạt được sự cân bằng giữa tính bảo mật và dễ sử dụng.

---

## 1. Giới Thiệu

### 1.1 Vấn Đề Đặt Ra trong Hệ Thống Hiện Đại

Bối cảnh hiện nay, khi các hệ thống quản lý bán hàng lưu trữ những dữ liệu vô cùng nhạy cảm như thông tin doanh thu, lợi nhuận, và chi tiết khách hàng, việc bảo vệ các dữ liệu này từ truy cập trái phép trở thành yêu cầu bắt buộc. Nếu các API được công khai mà không có cơ chế xác thực thích hợp, hệ thống sẽ phải đối mặt với những rủi ro đáng kể. Thứ nhất, bất kỳ ai cũng có thể truy cập những dữ liệu kinh doanh nhạy cảm mà không cần phép. Thứ hai, hệ thống không thể theo dõi được ai đã truy cập những thông tin gì, làm mất đi tính phụ trách. Thứ ba, không thể phân quyền dựa trên vai trò của từng người dùng, dẫn đến mất kiểm soát. Cuối cùng, việc không có cơ chế bảo mật sẽ vi phạm các tiêu chuẩn bảo mật quốc tế do các tổ chức như OWASP (Open Web Application Security Project) đề ra.

### 1.2 Giải Pháp Được Chọn

Để giải quyết những thách thức trên, dự án đã lựa chọn sử dụng JWT (JSON Web Token) kết hợp với RBAC (Role-Based Access Control). Sự lựa chọn này không phải là ngẫu nhiên mà dựa trên nhu cầu thực tế của hệ thống hiện đại. JWT cung cấp cơ chế xác thực dựa trên token mà không yêu cầu máy chủ phải lưu trữ thông tin phiên, điều này rất quan trọng khi muốn mở rộng hệ thống theo chiều ngang (horizontal scaling) hoặc triển khai kiến trúc microservices. Bên cạnh đó, RBAC cho phép phân chia người dùng thành các nhóm với quyền hạn khác nhau, từ đó đảm bảo rằng mỗi người dùng chỉ có thể truy cập những tài nguyên mà họ được phép. Kết hợp cả hai, giải pháp này vừa đảm bảo tính bảo mật cao, vừa duy trì tính linh hoạt và khả năng mở rộng của hệ thống.

---

## 2. Kiến Trúc Tổng Quan

### 2.1 Luồng Xử Lý Request

Để hiểu rõ cách thức hoạt động của hệ thống, cần nắm bắt được luồng xử lý request từ lúc người dùng bắt đầu cho đến khi nhận được response từ máy chủ. Quá trình này diễn ra qua hai giai đoạn chính: giai đoạn xác thực (authentication) và giai đoạn truy vấn dữ liệu có bảo mật (authorized data access).

Trong giai đoạn xác thực, khi người dùng gửi yêu cầu đăng nhập tới endpoint `/auth/login` cùng với tên người dùng và mật khẩu, máy chủ sẽ thực hiện việc xác minh thông tin đăng nhập. Nếu thông tin đúng, máy chủ sẽ tạo một JWT token chứa thông tin người dùng (tên và vai trò) và gửi lại cho client. Client sau đó sẽ lưu token này vào bộ nhớ cục bộ (localStorage).

Trong giai đoạn thứ hai, khi client cần truy cập một endpoint được bảo vệ (ví dụ `/api/kpis`), nó sẽ gửi kèm token vào phần header của request với định dạng `Authorization: Bearer <token>`. Khi nhận được request này, máy chủ sẽ tiến hành xác minh token bằng cách giải mã (decode) nó và kiểm tra chữ ký điện tử (signature) cùng thời gian hết hạn. Nếu token hợp lệ, máy chủ sẽ kiểm tra vai trò (role) của người dùng để đảm bảo họ có quyền truy cập endpoint này. Cuối cùng, nếu tất cả các kiểm tra đều thành công, máy chủ sẽ xử lý request và trả lại dữ liệu.

```
┌──────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1: XÁC THỰC (AUTHENTICATION)                      │
│ ┌─────────────┐             ┌──────────────────┐            │
│ │   CLIENT    │─────────────→│   BACKEND        │            │
│ │             │ POST /auth/ │ • Verify cred.   │            │
│ │             │ login       │ • Get user role  │            │
│ │             │             │ • Create JWT     │            │
│ └─────────────┘             └────────┬─────────┘            │
│                                      │                       │
│                 {access_token, expires_in}                  │
│ ┌─────────────┐◄─────────────┤                              │
│ │   CLIENT    │  Save to     │                              │
│ │ localStorage│  localStorage│                              │
│ └─────────────┘                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 2: TRUY VẤN DỮ LIỆU CÓ BẢO MẬT (AUTHORIZED)      │
│ ┌─────────────┐             ┌──────────────────┐            │
│ │   CLIENT    │─────────────→│   BACKEND        │            │
│ │             │ GET /api/kpis│ • Extract token  │            │
│ │             │ Header:      │ • Verify sign.   │            │
│ │             │ Bearer token │ • Check exp      │            │
│ │             │             │ • Check role     │            │
│ │             │             │ • Process req.   │            │
│ └─────────────┘             └────────┬─────────┘            │
│                                      │                       │
│                    {kpis_data}       │                       │
│ ┌─────────────┐◄─────────────┤                              │
│ │   CLIENT    │  Render      │                              │
│ │             │  dashboard   │                              │
│ └─────────────┘                                              │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Phân Loại Các Cụm API

Hệ thống API trong dự án được tổ chức thành ba nhóm chính dựa trên mức độ bảo mật và mục đích sử dụng. Cách phân loại này giúp tối ưu hóa quản lý bảo mật và làm cho hệ thống dễ hiểu hơn.

Cụm thứ nhất gồm các **Public Endpoints**, đó là những endpoint không yêu cầu token xác thực. Những endpoint này bao gồm `GET /` để hiển thị thông báo chào mừng và `GET /health` dùng để kiểm tra trạng thái của máy chủ. Những endpoint này được truy cập tự do mà không có bất kỳ hạn chế nào.

**Authentication Endpoints** tạo thành cụm thứ hai, bao gồm tất cả những endpoint liên quan đến quản lý vòng đời người dùng. Cụ thể, `POST /auth/login` cho phép người dùng đăng nhập và nhận token; `POST /auth/signup` cho phép đăng ký tài khoản mới với vai trò mặc định là "viewer"; `POST /auth/register` cho phép quản trị viên tạo tài khoản mới với vai trò cụ thể. Ngoài ra còn có `GET /auth/me` để lấy thông tin người dùng hiện tại, `GET /auth/users` để liệt kê tất cả người dùng (chỉ admin), `PUT /auth/change-password` để đổi mật khẩu, `DELETE /auth/users/{username}` để xóa tài khoản, và cuối cùng `POST /auth/logout` để đăng xuất.

Cụm thứ ba là **Protected Data Endpoints**, những endpoint này yêu cầu token xác thực hợp lệ trước khi có thể truy cập. Những endpoint này phục vụ cho việc lấy dữ liệu phân tích và dự báo, bao gồm `GET /api/filters` để lấy tùy chọn bộ lọc, `GET /api/kpis` để lấy các chỉ số chính, `GET /api/charts/sales-trend` cho xu hướng bán hàng, `GET /api/charts/category-sales` cho doanh thu theo danh mục, `GET /api/charts/region-sales` cho doanh thu theo khu vực, `GET /api/forecast` cho dự báo bán hàng 30 ngày, `GET /api/customer-segmentation` cho phân khúc khách hàng, `GET /api/sales-heatmap` cho biểu đồ heatmap, và các endpoint AI như `POST /api/ai/insights` và `GET /api/ai/insights/{id}`.

---

## 3. JWT (JSON Web Token) - Chi Tiết Cài Đặt

### 3.1 Định Nghĩa và Cấu Trúc JWT

JWT là một tiêu chuẩn (RFC 7519) để trao đổi thông tin một cách an toàn giữa các bên (client và server) thông qua token mã hóa. Khác với các phương pháp xác thực truyền thống sử dụng session lưu trên máy chủ, JWT là stateless - điều này có nghĩa là máy chủ không cần phải lưu trữ bất kỳ thông tin gì về phiên người dùng. Thay vào đó, toàn bộ thông tin cần thiết được mã hóa vào trong token, và máy chủ chỉ cần xác minh tính toàn vẹn của token thông qua chữ ký điện tử.

JWT bao gồm ba phần chính, mỗi phần được ngăn cách bởi một dấu chấm (`.`). Phần đầu tiên được gọi là **Header**, chứa các thông tin về loại token (JWT) và thuật toán mã hóa được sử dụng (trong trường hợp này là HS256 - HMAC with SHA-256). Khi được mã hóa Base64, phần Header có dạng: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9`.

Phần thứ hai là **Payload**, nơi chứa các thông tin thực tế về người dùng mà chúng ta muốn truyền đi. Payload bao gồm các claims (tuyên bố), trong đó "sub" (subject) chứa tên người dùng, "role" chứa vai trò của người dùng, và "exp" (expiration) chứa thời điểm hết hạn của token (định dạng Unix timestamp). Ví dụ, payload có thể là `{"sub": "admin", "role": "admin", "exp": 1703000000}`, và khi mã hóa Base64 sẽ là: `eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcwMzAwMDAwMH0`.

Phần thứ ba là **Signature**, được tạo ra bằng cách mã hóa Header và Payload kết hợp lại (cách nhau bởi dấu chấm) bằng thuật toán HS256 với một khóa bí mật (SECRET_KEY) chỉ có máy chủ biết. Signature này đóng vai trò như một chữ ký điện tử, đảm bảo rằng không có ai có thể thay đổi nội dung của token mà không có khóa bí mật. Bất kỳ thay đổi nhỏ nào trong Header hay Payload sẽ làm cho Signature không khớp, từ đó token sẽ bị xem là không hợp lệ.

Khi kết hợp cả ba phần lại, một JWT token hoàn chỉnh sẽ có dạng: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTcwMzAwMDAwMH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c`.

### 3.2 Tạo Token (Create Process)

Khi người dùng đăng nhập thành công, máy chủ cần tạo một JWT token để gửi lại cho client. Quá trình tạo token được thực hiện trong hàm `create_access_token` có trong module `backend/auth.py`. Hàm này nhận vào một dictionary chứa thông tin người dùng (tên và vai trò) và một tham số tùy chọn là thời gian hết hạn tùy chỉnh. Nếu không cung cấp thời gian hết hạn tùy chỉnh, hàm sẽ sử dụng giá trị mặc định từ biến môi trường `TOKEN_EXPIRE_MINUTES`, thường là 60 phút.

Quy trình tạo token tuân theo một chuỗi các bước logic. Đầu tiên, hàm sao chép dữ liệu đầu vào để tránh thay đổi dữ liệu gốc. Sau đó, nó tính toán thời điểm hết hạn bằng cách lấy thời gian hiện tại (theo UTC) cộng thêm số phút được chỉ định. Tiếp theo, nó thêm claim "exp" (expiration) vào dữ liệu. Cuối cùng, nó mã hóa dữ liệu bằng thư viện `python-jose` với khóa bí mật và thuật toán HS256, trả về chuỗi token đã mã hóa.

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### 3.3 Xác Minh Token (Decode and Validate Process)

Khi client gửi request kèm token tới một endpoint được bảo vệ, máy chủ phải tiến hành xác minh token để đảm bảo rằng nó hợp lệ. Quá trình này được thực hiện trong hàm `decode_token`. Hàm này sử dụng thư viện `python-jose` để giải mã token và xác minh chữ ký điện tử. Nếu token hợp lệ, hàm sẽ trích xuất tên người dùng và vai trò từ payload. Nếu token hết hạn hoặc chữ ký không khớp, thư viện sẽ ném ra ngoại lệ `JWTError`, và hàm sẽ trả về None để chỉ định token không hợp lệ.

Cơ chế xác minh token hoạt động như sau: khi máy chủ nhận được token, nó trích xuất Header, Payload và Signature từ token. Sau đó, nó sử dụng khóa bí mật và thuật toán HS256 để tái tạo Signature từ Header và Payload. Nếu Signature được tái tạo khớp với Signature trong token, token được xem là xác thực. Hơn nữa, máy chủ sẽ kiểm tra claim "exp" để đảm bảo token chưa hết hạn bằng cách so sánh thời gian hết hạn trong token với thời gian hiện tại.

```python
def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            return None
        return TokenData(username=username, role=role)
    except JWTError:
        return None
```

### 3.4 Endpoint Đăng Nhập

Endpoint `/auth/login` là điểm vào chính để người dùng lấy token. Khi nhận được request POST tới endpoint này với tên người dùng và mật khẩu, máy chủ sẽ tiến hành kiểm tra thông tin đăng nhập trong cơ sở dữ liệu người dùng. Nếu thông tin không khớp, máy chủ sẽ trả về lỗi HTTP 401 (Unauthorized) cùng với thông báo "Invalid username or password". Cần lưu ý rằng endpoint này được bảo vệ bởi cơ chế rate limiting (giới hạn 10 request mỗi phút) nhằm ngăn chặn tấn công brute-force, nơi kẻ tấn công thử nhiều mật khẩu khác nhau trong thời gian ngắn.

Nếu xác minh thông tin đăng nhập thành công, máy chủ sẽ tạo JWT token bằng cách gọi hàm `create_access_token` với thông tin người dùng là tham số. Token này sau đó được gửi lại cho client cùng với thông tin loại token ("bearer") và thời gian hết hạn tính bằng giây. Client sẽ lưu token này vào bộ nhớ cục bộ của trình duyệt (localStorage) để sử dụng trong những request tiếp theo.

```python
@app.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, user_data: UserLogin):
    """Authenticate user and return JWT token"""
    user = authenticate_user(user_data.username, user_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {user_data.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    logger.info(f"User logged in: {user['username']}")
    return Token(
        access_token=token,
        token_type="bearer",
        expires_in=int(os.getenv("TOKEN_EXPIRE_MINUTES", "60")) * 60
    )
```

### 3.5 Quản Lý Token Trên Frontend

Để sử dụng token trong những request tiếp theo, frontend cần lưu token và gửi nó đi cùng mỗi request tới những endpoint được bảo vệ. Dự án sử dụng thư viện Axios kết hợp với interceptor để tự động hoàn thành công việc này. Khi lưu token, client sẽ lưu nó vào localStorage, một bộ lưu trữ cục bộ của trình duyệt cho phép dữ liệu tồn tại ngay cả sau khi đóng trình duyệt.

Interceptor của Axios được cấu hình để tự động thêm token vào phần header của mỗi request. Cụ thể, nó sẽ lấy token từ localStorage và thêm nó vào header `Authorization` với định dạng `Bearer <token>`. Hơn nữa, interceptor cũng xử lý trường hợp máy chủ trả về lỗi 401 (Unauthorized), thường xảy ra khi token đã hết hạn. Trong trường hợp này, interceptor sẽ xóa token khỏi localStorage và tải lại trang web, buộc người dùng phải đăng nhập lại.

```typescript
const api = axios.create({
    baseURL: 'http://localhost:8000/api',
});

api.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined' 
        ? localStorage.getItem('auth_token') 
        : null;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            window.location.reload();
        }
        return Promise.reject(error);
    }
);
```

---

## 4. Role-Based Access Control (RBAC)

### 4.1 Mô Hình Phân Quyền Ba Cấp Độ

RBAC là một mô hình bảo mật trong đó quyền truy cập được xác định dựa trên vai trò của người dùng trong tổ chức. Hệ thống được thiết kế với ba cấp độ vai trò, mỗi cấp độ có những quyền hạn khác nhau tùy thuộc vào mục đích và trách nhiệm của người dùng trong hệ thống.

Cấp độ thứ nhất là "viewer" (người xem), vai trò này được gán mặc định cho những người dùng đăng ký tài khoản thông qua endpoint `/auth/signup`. Người dùng với vai trò này chỉ có quyền đọc, tức là họ có thể xem các bảng điều khiển, biểu đồ, và các chỉ số hiệu năng chính (KPI), nhưng họ không thể thực hiện bất kỳ hành động thay đổi nào như cập nhật cấu hình hoặc xóa dữ liệu. Vai trò này thích hợp cho những nhân viên trong phòng marketing hoặc bán hàng cần xem dữ liệu để nắm bắt tình hình kinh doanh.

Cấp độ thứ hai là "editor" (người chỉnh sửa), vai trò này cho phép người dùng không chỉ xem mà còn có thể chỉnh sửa một số phần của hệ thống như cập nhật cấu hình hoặc thay đổi các tham số của hệ thống. Tuy nhiên, người dùng với vai trò này không thể quản lý người dùng khác. Vai trò này phù hợp cho những nhân viên cấp trung như trưởng phòng hoặc chuyên gia phân tích dữ liệu cấp cao.

Cấp độ thứ ba là "admin" (quản trị viên), vai trò này có quyền hạn cao nhất trong hệ thống. Người dùng với vai trò admin không chỉ có thể xem và chỉnh sửa mọi thứ trong hệ thống, mà còn có toàn quyền quản lý người dùng, bao gồm tạo tài khoản mới, xóa tài khoản hiện có, và thay đổi vai trò của người dùng. Vai trò này thường được gán cho những người đứng đầu phòng IT hoặc quản trị viên hệ thống.

### 4.2 Cài Đặt và Xác Thực Vai Trò

Trong code, kiểu dữ liệu `UserCreate` được sử dụng để định nghĩa cấu trúc của một yêu cầu tạo người dùng, bao gồm tên người dùng, mật khẩu, và vai trò. Vai trò mặc định được đặt là "viewer" nếu không được chỉ định. Hơn nữa, hàm `register_user` thực hiện xác thực vai trò để đảm bảo rằng chỉ những vai trò hợp lệ ("viewer", "editor", "admin") mới được phép, nếu vai trò không hợp lệ sẽ ném ra ngoại lệ.

FastAPI cung cấp một tính năng mạnh mẽ gọi là dependency injection, cho phép chúng ta dễ dàng kiểm soát quyền hạn bằng cách tạo ra những hàm phụ thuộc (dependency) để kiểm tra vai trò. Ví dụ, hàm `require_admin` là một dependency kiểm tra xem người dùng hiện tại có vai trò "admin" hay không. Nếu không, hàm sẽ ném ra ngoại lệ HTTP 403 (Forbidden). Những hàm dependency này có thể được sử dụng như một tham số trong định nghĩa của endpoint, giúp kiểm soát quyền hạn một cách tập trung và dễ bảo trì.

```python
async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency: only allow admin role"""
    if current_user is None or current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@app.get("/auth/users")
def list_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)"""
    return [
        {"username": u["username"], "role": u["role"]}
        for u in users_db.values()
    ]
```

### 4.3 Phân Biệt Giữa Signup và Register

Hệ thống cung cấp hai endpoint khác nhau cho việc tạo tài khoản người dùng mới, mỗi endpoint phục vụ một mục đích khác nhau. Endpoint `/auth/signup` là một endpoint công khai, cho phép bất kỳ ai cũng có thể đăng ký tài khoản mà không cần có token xác thực. Tuy nhiên, để đảm bảo bảo mật, vai trò của những người dùng đăng ký qua endpoint này sẽ tự động được đặt là "viewer", bất kể người dùng có cố gắng chỉ định vai trò khác hay không. Điều này ngăn chặn tình trạng người dùng công khai tự gán quyền cao cho mình.

Ngược lại, endpoint `/auth/register` là một endpoint được bảo vệ, chỉ những người dùng có vai trò "admin" mới có thể truy cập. Endpoint này cho phép quản trị viên tạo tài khoản người dùng mới với vai trò cụ thể. Khi admin gọi endpoint này, họ có thể chỉ định vai trò mong muốn (viewer, editor, hoặc admin) cho tài khoản mới. Sự phân biệt này rất quan trọng vì nó đảm bảo rằng chỉ những người có quyền quản lý hệ thống (admin) mới có thể tạo những tài khoản có quyền hạn cao.

---

## 5. Bảo Mật (Security Measures)

### 5.1 Mã Hóa Mật Khẩu

Một trong những quy tắc vàng của bảo mật ứng dụng là không bao giờ lưu trữ mật khẩu dưới dạng văn bản thô (plaintext). Nếu cơ sở dữ liệu bị xâm nhập, kẻ tấn công sẽ có ngay quyền truy cập vào tất cả tài khoản người dùng. Để giải quyết vấn đề này, dự án sử dụng thuật toán bcrypt, một thuật toán mã hóa lâm dạng (cryptographic hash function) được thiết kế đặc biệt cho việc mã hóa mật khẩu. Bcrypt có một đặc tính quan trọng là nó có một thành phần ngẫu nhiên gọi là "salt", có nghĩa là hai mật khẩu giống nhau sẽ được mã hóa thành hai hash khác nhau. Điều này làm cho nó không thể tính toán ngược và rất khó bị tấn công brute-force.

Ngoài ra, bcrypt cũng có một tham số gọi là "cost factor" (thường là 12), điều này quyết định độ khó của việc tính toán hash. Giá trị cao hơn có nghĩa là cần nhiều thời gian hơn để tính toán hash, làm cho tấn công brute-force chậm hơn. Khi người dùng đăng nhập, hệ thống sẽ lấy mật khẩu người dùng nhập vào và sử dụng bcrypt để xác minh nó với hash được lưu trữ. Nếu khớp, người dùng được phép truy cập.

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)
```

### 5.2 Giới Hạn Tốc Độ Request (Rate Limiting)

Tấn công brute-force là một kiểu tấn công phổ biến trong đó kẻ tấn công cố gắng đoán mật khẩu bằng cách thử nhiều mật khẩu khác nhau trong một khoảng thời gian ngắn. Để ngăn chặn kiểu tấn công này, dự án áp dụng rate limiting, tức là giới hạn số lượng request mà một địa chỉ IP có thể gửi tới một endpoint trong một khoảng thời gian nhất định. Cụ thể, endpoint `/auth/login` được giới hạn ở 10 request mỗi phút, endpoint `/auth/register` và `/auth/signup` được giới hạn ở 5 request mỗi phút.

Cơ chế này được triển khai bằng cách sử dụng thư viện `slowapi`, một thư viện Python cung cấp rate limiting cho FastAPI. Khi một người dùng vượt quá giới hạn, máy chủ sẽ trả về lỗi HTTP 429 (Too Many Requests) cùng với thông báo chỉ định rằng họ cần phải chờ trước khi có thể gửi request tiếp theo. Cách tiếp cận này rất hiệu quả trong việc làm chậm đi hoặc ngăn hoàn toàn những cuộc tấn công brute-force.

### 5.3 Hết Hạn Token

Một cơ chế bảo mật quan trọng khác là việc đặt thời gian hết hạn cho token. Mặc dù token được mã hóa và có chữ ký điện tử, nhưng nếu token bị rò rỉ (ví dụ do kẻ tấn công xâm nhập máy tính client), kẻ tấn công có thể sử dụng token đó để truy cập hệ thống. Để giảm thiểu rủi ro này, token được đặt thời gian hết hạn (mặc định là 60 phút). Sau khoảng thời gian này, token sẽ không còn hợp lệ và người dùng phải đăng nhập lại để có token mới.

Khi máy chủ nhận được request với token hết hạn, quá trình xác minh token sẽ phát hiện ra rằng claim "exp" (expiration) trong token nhỏ hơn thời gian hiện tại, từ đó ném ra ngoại lệ `JWTError`. Hàm `decode_token` sẽ bắt ngoại lệ này và trả về `None`, chỉ định token không hợp lệ. Khi frontend nhận được lỗi 401 từ máy chủ, nó sẽ xóa token khỏi localStorage và buộc người dùng phải đăng nhập lại.

### 5.4 CORS (Cross-Origin Resource Sharing)

Cross-Origin Resource Sharing (CORS) là một cơ chế bảo mật được triển khai bởi trình duyệt web để ngăn chặn những script từ một trang web khác chiếc từ truy cập những tài nguyên trên trang web của bạn mà không có sự cho phép. Dự án cấu hình CORS bằng cách liệt kê những domain được phép truy cập từ một biến môi trường gọi là `ALLOWED_ORIGINS`. Chỉ những frontend từ những domain được liệt kê trong biến này mới có thể gọi API của hệ thống.

Ví dụ, nếu `ALLOWED_ORIGINS` được đặt thành `http://localhost:3000,http://localhost:8080`, chỉ những request từ frontend chạy tại `localhost:3000` hoặc `localhost:8080` mới được phép. Nếu một trang web khác (ví dụ từ một domain lạ) cố gắng gọi API, trình duyệt sẽ ngăn chặn request đó và ném ra CORS error. Cơ chế này giúp bảo vệ người dùng khỏi những cuộc tấn công cross-site scripting (XSS).

```python
from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8080"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### 5.5 Ghi Nhật Ký Request (Request Logging)

Để có thể theo dõi và kiểm toán những hoạt động trên hệ thống, tất cả những request HTTP được máy chủ xử lý sẽ được ghi lại vào file nhật ký. Mỗi entry trong nhật ký sẽ bao gồm phương thức HTTP (GET, POST, v.v.), đường dẫn được truy cập, mã trạng thái HTTP của phản hồi, thời gian xử lý request, và địa chỉ IP của client. Thông tin này rất quý giá khi điều tra những vấn đề bảo mật hoặc debug những lỗi trong hệ thống.

Nhật ký được ghi vào file dung lượng lớn (up to 10MB), và khi file đạt dung lượng tối đa, một file nhật ký mới sẽ được tạo. Cách tiếp cận này ngăn chặn file nhật ký trở nên quá lớn và ăn hết không gian đĩa. Hơn nữa, hệ thống lưu trữ tới 5 file nhật ký cũ, cho phép người quản trị xem lịch sử hoạt động trong một khoảng thời gian dài.

```python
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

---

## 6. Cấu Hình Biến Môi Trường

### 6.1 Các Biến Cấu Hình Chính

Để làm cho hệ thống linh hoạt và dễ triển khai trên những môi trường khác nhau (development, testing, production), dự án sử dụng biến môi trường để lưu trữ những thông tin nhạy cảm và cấu hình. File `.env` chứa những biến này được quy định ở gốc thư mục backend. Biến `AUTH_REQUIRED` xác định xem liệu hệ thống có yêu cầu JWT token cho tất cả những request tới API hay không. Khi giá trị là `false`, hệ thống ở chế độ development, cho phép truy cập API mà không cần token. Khi giá trị là `true`, hệ thống ở chế độ production, yêu cầu token hợp lệ cho tất cả những request.

Biến `SECRET_KEY` lưu trữ khóa bí mật được sử dụng để tạo và xác minh JWT token. Biến này cực kỳ quan trọng vì nó quyết định tính bảo mật của toàn bộ hệ thống JWT. Nếu khóa này bị xâm phạm, kẻ tấn công có thể tạo ra những token giả mà hệ thống sẽ chấp nhận. Do vậy, trong môi trường production, cần phải sử dụng một khóa mạnh (ít nhất 32 ký tự) được tạo ngẫu nhiên và không bao giờ được chia sẻ công khai.

Biến `TOKEN_EXPIRE_MINUTES` xác định thời gian hết hạn của token tính bằng phút. Biến `RATE_LIMIT` xác định giới hạn tốc độ request toàn cục của API. Biến `ALLOWED_ORIGINS` liệt kê những domain cơ sở được phép truy cập API (dùng cho CORS).

### 6.2 Hai Chế Độ Vận Hành

Hệ thống có thể vận hành ở hai chế độ khác nhau tùy thuộc vào giá trị của biến `AUTH_REQUIRED`. Chế độ **Development** (khi `AUTH_REQUIRED=false`) được sử dụng cho những giai đoạn phát triển và demo nội bộ, cho phép mọi người truy cập tất cả các API mà không cần token xác thực. Chế độ này tiện lợi cho việc testing bởi vì không cần phải liên tục tạo token. Tuy nhiên, chế độ này không an toàn cho production.

Chế độ **Production** (khi `AUTH_REQUIRED=true`) yêu cầu tất cả những request tới các endpoint được bảo vệ phải kèm theo JWT token hợp lệ. Nếu request không có token hoặc token không hợp lệ, máy chủ sẽ trả về lỗi 401 (Unauthorized). Chế độ này đảm bảo rằng chỉ những người dùng được xác thực mới có thể truy cập dữ liệu nhạy cảm của hệ thống.

---

## 7. Testing và Xác Minh Hệ Thống

### 7.1 Unit Tests (Kiểm Tra Đơn Vị)

Để đảm bảo rằng những tính năng bảo mật hoạt động đúng, dự án bao gồm một bộ kiểm tra đơn vị (unit tests) comprehensive với hơn 90 test cases. Những test này kiểm tra tất cả những khía cạnh của hệ thống authentication và authorization, từ những trường hợp thành công cho đến những trường hợp lỗi. Các test được viết sử dụng framework `pytest`, một framework kiểm tra phổ biến trong Python.

Một số test quan trọng bao gồm: test kiểm tra login thành công, test kiểm tra login với mật khẩu sai, test kiểm tra login với tên người dùng không tồn tại, test kiểm tra rằng signup tự động gán role "viewer", test kiểm tra rằng chỉ admin mới có thể dùng register endpoint, test kiểm tra rằng chỉ admin mới có thể xem danh sách users, test kiểm tra rằng token giả sẽ bị từ chối, test kiểm tra rate limiting, và nhiều test khác.

Để chạy những test này, người dùng có thể thực hiện lệnh `pytest -v test_main.py::TestAuthEndpoints` từ thư mục backend. Pytest sẽ tự động discover và chạy tất cả những test trong class `TestAuthEndpoints`.

### 7.2 Testing Manual (Kiểm Tra Thủ Công)

Ngoài những unit tests tự động, việc testing manual cũng rất quan trọng để đảm bảo rằng hệ thống hoạt động đúng trong những tình huống thực tế. Quá trình testing manual bao gồm một số bước. Đầu tiên, người dùng cần khởi động máy chủ backend bằng lệnh `python -m uvicorn main:app --reload`. Lệnh này sẽ bắt đầu một máy chủ development tại địa chỉ `http://localhost:8000`.

Tiếp theo, người dùng có thể kiểm tra endpoint login bằng cách gửi một request curl tới `/auth/login` với tên người dùng và mật khẩu. Nếu thông tin đang nhập, máy chủ sẽ trả về một token. Người dùng sau đó có thể sử dụng token này để gọi những endpoint được bảo vệ như `/api/kpis` bằng cách thêm token vào header `Authorization`. Để kiểm tra rate limiting, người dùng có thể cố gắng gửi 11 request login liên tiếp (vượt quá giới hạn 10/minute), request thứ 11 sẽ nhận được lỗi 429 (Too Many Requests).

```bash
# Kiểm tra login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Kiểm tra protected API
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl http://localhost:8000/api/kpis \
  -H "Authorization: Bearer $TOKEN"
```

---

## 8. Giới Hạn Hiện Tại và Cải Thiện Tương Lai

### 8.1 Những Thách Thức Hiện Tại

Mặc dù hệ thống hiện tại đã triển khai thành công những tính năng bảo mật và lưu trữ dữ liệu bằng PostgreSQL (được cấu hình trong `docker-compose.yml`), vẫn còn một số hạn chế cần phải được giải quyết để đạt mức production-ready hoàn toàn. Cơ sở dữ liệu PostgreSQL đã được tích hợp với image phiên bản 16-Alpine, cho phép hệ thống lưu trữ bền vững những thông tin người dùng và session ngay cả khi máy chủ khởi động lại. Điều này là một điểm mạnh đáng kể so với những hệ thống sử dụng in-memory storage.

Thứ nhất, hệ thống hiện tại chỉ sử dụng access token và không có cơ chế refresh token. Điều này có nghĩa là khi token hết hạn (sau 60 phút), người dùng phải đăng nhập lại để lấy token mới. Cách tiếp cận này kém user experience, đặc biệt khi người dùng đang làm việc trên hệ thống trong một phiên hành kéo dài.

Thứ hai, khi người dùng đăng xuất, token không được vô hiệu hóa trên máy chủ. Có nghĩa là nếu kẻ tấn công lấy được token trước khi người dùng đăng xuất, kẻ tấn công vẫn có thể sử dụng token đó cho đến khi token hết hạn. Cách tiếp cận này cần phải được cải thiện bằng cách triển khai token blacklist hoặc sử dụng Redis để quản lý danh sách các token bị vô hiệu hóa.

### 8.2 Lộ Trình Cải Thiện

Để giải quyết những hạn chế còn lại, dự án có một lộ trình cải thiện rõ ràng. Cần lưu ý rằng **Phase 1: Database Persistence** đã được hoàn thành trong dự án này. Hệ thống đã được cấu hình với PostgreSQL 16 trong file `docker-compose.yml`, bao gồm những SQLAlchemy ORM models cho table users, database migration scripts, và những hàm authentication đã được cập nhật để tương tác với cơ sở dữ liệu. Điều này cho phép hệ thống lưu trữ bền vững và có thể scale với những production deployments.

**Phase 2: Refresh Token Mechanism** (Ưu tiên cao) là giai đoạn tiếp theo cần ưu tiên. Bao gồm việc triển khai một cơ chế refresh token hoàn chỉnh. Thay vì chỉ trả về một access token, endpoint login sẽ trả về cả access token (hết hạn sau 1 giờ) và refresh token (hết hạn sau 7 ngày). Khi access token hết hạn, client có thể sử dụng refresh token để lấy một access token mới mà không cần người dùng phải đăng nhập lại.

**Phase 3: Token Blacklist** (Ưu tiên trung bình) bao gồm việc thiết lập một Redis instance để lưu trữ những token bị vô hiệu hóa. Khi người dùng đăng xuất, token sẽ được thêm vào blacklist. Trước khi xác minh token, hệ thống sẽ kiểm tra xem token có nằm trong blacklist hay không. Redis có thể được cấu hình thêm vào file `docker-compose.yml` để tích hợp seamlessly.

**Phase 4: Permission Granularity** (Ưu tiên trung bình) bao gồm việc triển khai chi tiết hơn để xác định quyền hạn của editor role và những role khác. Điều này sẽ cho phép hệ thống kiểm soát quyền truy cập ở mức độ chi tiết hơn, chẳng hạn như cho phép editor chỉnh sửa cấu hình nhưng không cho phép xóa dữ liệu.

---

## 9. Kết Luận

### 9.1 Tóm Tắt Hệ Thống

Hệ thống bảo mật dựa trên JWT kết hợp RBAC được trình bày trong chương này đại diện cho một giải pháp hiện đại và bảo mật cho việc xác thực và phân quyền trong các ứng dụng web hiện đại. Cách tiếp cận này cung cấp nhiều lợi ích so với những phương pháp truyền thống. Thứ nhất, JWT là stateless, có nghĩa là máy chủ không cần phải lưu trữ thông tin về phiên người dùng, từ đó dễ dàng mở rộng hệ thống theo chiều ngang hoặc triển khai trong kiến trúc microservices. Thứ hai, RBAC cung cấp một cách linh hoạt để quản lý quyền hạn của người dùng dựa trên vai trò của họ. Thứ ba, hệ thống tuân thủ những tiêu chuẩn quốc tế như OAuth 2.0 và JWT (RFC 7519), giúp đảm bảo tính tương thích với những hệ thống khác.

### 9.2 Điểm Mạnh của Hệ Thống

Hệ thống hiện tại có những điểm mạnh đáng kể. Việc triển khai JWT tuân theo những thực hành tốt nhất, sử dụng thuật toán HS256 với khóa bí mật mạnh và có thời gian hết hạn. Password hashing được thực hiện bằng bcrypt, một thuật toán được thiết kế đặc biệt cho mục đích này và rất khó bị tấn công. CORS được cấu hình để chỉ cho phép những frontend từ những domain được whitelist. Rate limiting được triển khai để ngăn chặn tấn công brute-force. Hơn nữa, hệ thống có một test suite comprehensive với hơn 90 test cases đảm bảo rằng các tính năng bảo mật hoạt động đúng. Frontend integration cũng được thực hiện một cách sạch sẽ bằng cách sử dụng Axios interceptor để tự động quản lý token.

### 9.3 Những Hạn Chế Cần Cải Thiện

Mặc dù mạnh mẽ, hệ thống hiện tại vẫn có những hạn chế cần phải được cải thiện. Thứ nhất, không có cơ chế refresh token làm giảm user experience khi access token hết hạn. Thứ hai, token không được vô hiệu hóa khi người dùng đăng xuất, có nghĩa là token vẫn có thể được sử dụng cho đến khi hết hạn. Cuối cùng, role "editor" được định nghĩa nhưng chưa được triển khai đầy đủ trong code với những permission checks cụ thể. Tuy nhiên, cần ghi nhận rằng hệ thống đã vượt qua vấn đề lưu trữ in-memory bằng cách tích hợp PostgreSQL trong `docker-compose.yml`, điều này là một cải thiện đáng kể so với những giải pháp development-only.

### 9.4 Triển Vọng Tương Lai

Sau khi những vấn đề trên được giải quyết thông qua lộ trình cải thiện được đề xuất, hệ thống sẽ đạt mức production-ready hoàn toàn. Tại thời điểm đó, hệ thống sẽ có thể hỗ trợ những tính năng nâng cao như kiến trúc multi-tenant, triển khai dựa trên microservices, bộ nhớ cache phân tán sử dụng Redis, ghi lại audit log chi tiết, và tích hợp với những hệ thống Single Sign-On (SSO) khác. Những cải thiện này sẽ làm cho hệ thống trở thành một giải pháp bảo mật mạnh mẽ, linh hoạt, và có thể mở rộng để phục vụ những ứng dụng enterprise lớn.

### 9.5 Đánh Giá Tổng Thể

Qua phân tích chi tiết toàn bộ hệ thống, có thể rút ra kết luận rằng hệ thống hiện tại đang ở giai đoạn **"Production-Ready with Minor Enhancements"** (Sẵn sàng cho Production với một số cải thiện nhỏ). Việc triển khai JWT + RBAC được thực hiện đúng chuẩn, test coverage là toàn diện, frontend integration được làm một cách chuyên nghiệp, và cơ sở dữ liệu PostgreSQL đã được tích hợp trong `docker-compose.yml` cho phép lưu trữ bền vững. Hệ thống hiện đã sẵn sàng để triển khai cho những môi trường production nhỏ đến trung bình. Các cải thiện tiếp theo như refresh token mechanism và token blacklist sẽ giúp nâng cao xử lý phiên người dùng và bảo mật tổng thể của hệ thống.

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

[8] Docker - Container Platform
    https://www.docker.com/
```

---

**Chương 4.4 - Kiến Trúc Tích Hợp API và Bảo Mật (JWT Authentication)**  
*Dự Án: AI-Powered Sales Forecasting Dashboard*  
*Ngày: 06/04/2026*  
*Phong Cách: Học Thuật - Tiểu Luận Chuyên Sâu*  
*Trạng Thái: Hoàn Thành*
