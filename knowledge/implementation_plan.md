# Enhance AI Chatbot to Answer Based on CSV Data

Chatbot hiện tại ([InsightsAssistant.tsx](file:///c:/Users/LENOVO/source/repos/specialized-projects%282%29/frontend/components/InsightsAssistant.tsx)) gửi câu hỏi đến backend `/api/ai/chat`, backend chỉ truyền **analysis bundle đã tính toán sẵn** (KPIs, forecast, RFM, etc.) cho OpenAI. System prompt rất đơn giản ("You are a BI copilot") — không có dữ liệu CSV thực tế nào, không có chỉ dẫn trả lời ngắn gọn/tập trung.

**Mục tiêu**: Chatbot phải trả lời dựa trên dữ liệu CSV thực tế, đưa ra đánh giá khi được hỏi, và trả lời tập trung — không vòng vo.

## Proposed Changes

### Backend ([main.py](file:///c:/Users/LENOVO/source/repos/specialized-projects%282%29/backend/main.py))

#### [MODIFY] [main.py](file:///c:/Users/LENOVO/source/repos/specialized-projects(2)/backend/main.py)

**1. Thêm raw CSV sample data vào context của `/api/ai/chat` (line ~1325-1366)**

Hiện tại context chỉ có analysis bundle (KPIs, forecast, etc.). Sẽ thêm:
- Đọc raw CSV data (đã filter) và lấy sample 50 dòng đại diện
- Truyền cả column names + sample rows vào context cho LLM
- LLM sẽ có dữ liệu thực để tra cứu và đưa ra đánh giá cụ thể

```diff
 context = {
     "kpis": analysis_run.get("computed_kpis_json", {}),
     ...
+    "raw_data_sample": [...],  # 50 sample rows from filtered CSV
+    "total_records": ...,      # Total records in filtered dataset
+    "column_names": [...],     # All column names
 }
```

**2. Cải thiện system prompt của `/api/ai/chat`**

System prompt hiện tại chỉ có 1 dòng generic. Sẽ thay bằng prompt chi tiết:
- Yêu cầu trả lời **dựa trên dữ liệu thực** (không bịa số)
- Trả lời **ngắn gọn, tập trung** vào câu hỏi
- **Đưa ra đánh giá** khi người dùng hỏi (không chỉ liệt kê số)
- Sử dụng tiếng Việt khi người dùng hỏi tiếng Việt
- Trả lời dạng bullet point khi phù hợp

**3. Cải thiện system prompt của `/api/ai/insights` (line ~1271-1284)**

Tương tự, thêm raw data sample vào evidence và cải thiện prompt để insights tập trung, có đánh giá rõ ràng.

---

### Frontend ([InsightsAssistant.tsx](file:///c:/Users/LENOVO/source/repos/specialized-projects%282%29/frontend/components/InsightsAssistant.tsx))

#### [MODIFY] [InsightsAssistant.tsx](file:///c:/Users/LENOVO/source/repos/specialized-projects(2)/frontend/components/InsightsAssistant.tsx)

**1. Hiển thị followup suggestions sau câu trả lời**

API trả về `followups` nhưng frontend hiện không sử dụng. Sẽ hiển thị các suggestion buttons sau mỗi câu trả lời của assistant.

**2. Cải thiện markdown rendering cho câu trả lời**

Hiện tại chat message chỉ hiển thị text thuần. Sẽ parse markdown cơ bản (bullet points, bold, numbers).

**3. Cập nhật suggested prompts phù hợp hơn**

Thêm các prompt gợi ý liên quan đến đánh giá dữ liệu CSV.

---

### Frontend API ([api.ts](file:///c:/Users/LENOVO/source/repos/specialized-projects%282%29/frontend/lib/api.ts))

#### [MODIFY] [api.ts](file:///c:/Users/LENOVO/source/repos/specialized-projects(2)/frontend/lib/api.ts)

Cập nhật interface [AIChatResponse](file:///c:/Users/LENOVO/source/repos/specialized-projects%282%29/frontend/lib/api.ts#126-130) để sử dụng `followups` field (đã có sẵn).

## Verification Plan

### Existing Tests
- File [backend/test_main.py](file:///c:/Users/LENOVO/source/repos/specialized-projects%282%29/backend/test_main.py) có 90+ test cases nhưng **không có test cho `/api/ai/chat` hay `/api/ai/insights`** (các endpoint này yêu cầu PostgreSQL + OpenAI)

### Manual Verification
1. **Khởi động backend**: `cd backend && python -m uvicorn main:app --reload`
2. **Khởi động frontend**: `cd frontend && npm run dev`
3. **Mở browser** tại `http://localhost:3000`
4. **Login** và chọn filter date range → nhấn reload data
5. **Vào tab Chat** trong InsightsAssistant panel
6. **Gửi câu hỏi test**:
   - "Category nào có doanh thu cao nhất?" → Chatbot phải trả lời cụ thể dựa trên dữ liệu CSV
   - "Đánh giá tình hình kinh doanh hiện tại" → Chatbot phải đưa ra đánh giá tập trung, có số liệu
   - "Region nào cần cải thiện?" → Chatbot phải so sánh và đánh giá
7. **Kiểm tra followup suggestions** có hiển thị sau câu trả lời

> [!IMPORTANT]
> Cần có PostgreSQL chạy và `OPENROUTER_API_KEY` (hoặc `OPENAI_API_KEY`) được cấu hình trong [.env](file:///c:/Users/LENOVO/source/repos/specialized-projects%282%29/backend/.env) để test được AI chat. Nếu không có, chatbot sẽ fallback về message lỗi.
