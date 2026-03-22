# PRD — AI-Powered Sales Forecasting Dashboard
**Version:** 1.0 | **Date:** 2026-03-03 | **Status:** Final Draft  
**Role:** Business Analyst | **Phase:** Finalization (đóng gói sản phẩm)

---

## Mục tiêu tài liệu

PRD này là **nguồn sự thật duy nhất (Single Source of Truth)** cho giai đoạn hoàn thiện sản phẩm. Không vẽ lại từ đầu — chỉ **lấp đầy khoảng trống** để hệ thống đủ điều kiện demo và bảo vệ đồ án.

**Scope:** 4 nhóm tính năng cần hoàn thiện:
1. Global Filtering & State Management
2. Sales Heatmap UI
3. Customer Table + Export CSV
4. Backend Refactoring (Cache + Utils)

---

## Personas

| Persona | Mô tả | Mục tiêu chính |
|---|---|---|
| **Quản lý kinh doanh** | Không rành kỹ thuật, cần số liệu nhanh | Xem KPI + xu hướng mỗi sáng |
| **Nhân viên Marketing** | Cần danh sách khách hàng theo nhóm | Lọc và export nhóm "At Risk" để chạy chiến dịch |
| **Người demo/bảo vệ đồ án** | Cần hệ thống chạy trơn tru, đầy đủ tính năng | Không bị lỗi, biểu đồ đầy đủ, luồng mượt |

---

## FEATURE 1 — Global Filtering & State Management

### Bối cảnh
Hiện tại, bộ lọc bị reset khi chuyển trang Dashboard ↔ Customer Insights. Mỗi component tự gọi API riêng lẻ.

### User Story
> **Là** người dùng, **tôi muốn** bộ lọc (Date, Region, Category) được giữ nguyên khi tôi chuyển trang, **để** tôi không phải chọn lại bộ lọc mỗi lần.

### Functional Requirements

| ID | Yêu cầu |
|---|---|
| FR-1.1 | Bộ lọc Date Range, Region, Category đặt ở Header, hiển thị trên cả 2 trang |
| FR-1.2 | Trạng thái bộ lọc lưu trong React Context (`GlobalFilterContext`) |
| FR-1.3 | Khi bộ lọc thay đổi, tất cả API liên quan tự động gọi lại với params mới |
| FR-1.4 | Trong khi chờ API, hiển thị **Skeleton Loading** (không dùng spinner xoay) |
| FR-1.5 | Giá trị mặc định: Date = Last 30 days, Region = All, Category = All |

### Acceptance Criteria

- [ ] **AC-1.1:** Chọn Region "West" ở Dashboard → chuyển sang Customer Insights → Region vẫn là "West"
- [ ] **AC-1.2:** Thay đổi bất kỳ bộ lọc → tất cả biểu đồ reload trong vòng 3 giây
- [ ] **AC-1.3:** Trong lúc loading, vùng biểu đồ hiển thị skeleton xám mờ, không hiển thị dữ liệu cũ

---

## FEATURE 2 — Sales Calendar Heatmap UI

### Bối cảnh
API `/api/sales-heatmap` đã hoạt động trả về `[{ day: "2023-01-01", value: 100 }]`. Frontend **chưa render** thành biểu đồ.

### User Story
> **Là** quản lý kinh doanh, **tôi muốn** thấy biểu đồ heatmap dạng lịch để nhận ra ngày/tháng nào có doanh thu cao/thấp, **để** lên kế hoạch nhập hàng theo mùa vụ.

### Functional Requirements

| ID | Yêu cầu |
|---|---|
| FR-2.1 | Render Calendar Heatmap ở Row 3, trang Dashboard (cạnh Category Sales chart) |
| FR-2.2 | Dùng thư viện `react-calendar-heatmap` hoặc Chart.js Matrix plugin |
| FR-2.3 | Màu sắc: xanh nhạt (thấp) → xanh đậm (cao). Ngày không có data → màu xám |
| FR-2.4 | Hover vào ô ngày → tooltip: "Ngày DD/MM/YYYY — Doanh thu: X VND" |
| FR-2.5 | Heatmap phản hồi bộ lọc Global (Category, Region, Date Range) |

### Acceptance Criteria

- [ ] **AC-2.1:** Mở trang Dashboard → thấy biểu đồ heatmap, không lỗi render
- [ ] **AC-2.2:** Hover vào ô → tooltip hiện đúng ngày và giá trị
- [ ] **AC-2.3:** Lọc Category = "Technology" → heatmap cập nhật đúng dữ liệu
- [ ] **AC-2.4:** Ngày không có dữ liệu → ô xám nhạt, không crash

---

## FEATURE 3 — Customer Table + Export CSV

### Bối cảnh
Trang Customer Insights có Pie chart và Bubble chart nhưng thiếu bảng danh sách và chức năng xuất file cho Marketing.

### User Stories

> **US-3A:** **Là** nhân viên Marketing, **tôi muốn** lọc danh sách khách hàng theo phân khúc, **để** biết chính xác ai cần liên hệ.

> **US-3B:** **Là** nhân viên Marketing, **tôi muốn** xuất danh sách ra file CSV, **để** import vào công cụ email marketing.

### Functional Requirements

| ID | Yêu cầu |
|---|---|
| FR-3.1 | Hiển thị bảng danh sách khách hàng bên dưới biểu đồ trang `/customers` |
| FR-3.2 | Cột: Customer ID, Customer Name, Recency (ngày), Frequency (lần), Monetary (VND), Segment, Action |
| FR-3.3 | Dropdown "Filter by Segment": All / Champions / Loyal / At Risk / New Customers |
| FR-3.4 | Nút **"Export CSV"** xuất dữ liệu đang hiển thị — xử lý Client-side, không gọi thêm API |
| FR-3.5 | Tên file: `customer_segment_[SegmentName]_[YYYY-MM-DD].csv` |
| FR-3.6 | Cột Action: Champions → "Gửi Voucher VIP", At Risk → "Gửi Email Nhắc", Loyal → "Upsell", New → "Onboarding" |

### Acceptance Criteria

- [ ] **AC-3.1:** Trang `/customers` hiển thị bảng với đủ 5 cột trên
- [ ] **AC-3.2:** Chọn Segment "At Risk" → bảng chỉ hiện khách hàng At Risk
- [ ] **AC-3.3:** Nhấn "Export CSV" → trình duyệt tải xuống file, nội dung khớp bảng đang hiển thị
- [ ] **AC-3.4:** File CSV có header row đúng định dạng
- [ ] **AC-3.5:** Không có thêm request lên backend khi export

---

## FEATURE 4 — Backend Refactoring (Cache + Utils)

### Bối cảnh
Logic lọc dữ liệu lặp lại ở 6 endpoint. Mỗi request đọc lại CSV từ đầu.

### User Story (Technical)
> **Là** developer, **tôi muốn** có hàm lọc dùng chung và dữ liệu được cache khi khởi động, **để** code dễ bảo trì và API nhanh hơn.

### Functional Requirements

| ID | Yêu cầu |
|---|---|
| FR-4.1 | Tạo `backend/utils.py` với hàm `filter_data(df, category, region, start_date, end_date) -> DataFrame` |
| FR-4.2 | Tất cả 7 endpoint gọi `filter_data()` thay vì viết `if/else` riêng |
| FR-4.3 | Load CSV **một lần duy nhất** khi startup (`@app.on_event("startup")`), lưu vào `global_df` |
| FR-4.4 | Nếu data sau lọc < 30 dòng, `/api/forecast` trả về `{"warning": "Không đủ dữ liệu"}` thay vì chạy Prophet |
| FR-4.5 | Gán nhãn KMeans dựa trên centroid trung bình, không hardcode cluster ID |

### Acceptance Criteria

- [ ] **AC-4.1:** `utils.py` tồn tại, `filter_data()` hoạt động đúng với cả 4 tham số
- [ ] **AC-4.2:** [main.py](file:///d:/Nam-4/HK2/DoAnChuyenNganh-Dat/DO-AN-CHUYEN-NGANH/AI-Powered-Sales-Forecasting-Dashboard/backend/main.py) không còn block `if category: df = df[...]` lặp lại
- [ ] **AC-4.3:** Khởi động server → log có dòng "Data loaded successfully"
- [ ] **AC-4.4:** Gọi `/api/forecast` với ít data → nhận JSON có key `warning`
- [ ] **AC-4.5:** Chạy `/api/customer-segmentation` nhiều lần → nhãn Champions/At Risk luôn nhất quán

---

## Tóm Tắt Scope & Priority

| Feature | Priority | Ước tính | Phụ thuộc |
|---|---|---|---|
| F4 — Backend Refactor | 🔴 High | 0.5 ngày | Làm trước tất cả |
| F1 — Global Filter State | 🔴 High | 0.5 ngày | Sau F4 |
| F3 — Customer Table + Export | 🔴 High | 1 ngày | Sau F4 |
| F2 — Calendar Heatmap UI | 🟡 Medium | 1 ngày | Sau F4 |

> **Tổng:** ~3 ngày để hoàn thiện 15–25% còn lại.

---

## Out of Scope

- Email Alerts tự động
- Authentication / Login
- Biểu đồ Sankey
- Dự báo theo từng phân khúc
- Triển khai lên cloud production

---

> **Nguyên tắc:** Mọi thay đổi code phải có ticket tương ứng trong PRD này. Tính năng ngoài scope → tạo PRD v1.1, không sửa trực tiếp file này.
