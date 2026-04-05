# AI Chart Click Insights — Spec (Project-local)

## Goal
When a user clicks any chart on the dashboard, the system generates an AI insight for that chart (summary, anomalies, possible causes, recommended actions) in a few seconds, displayed in a side panel.

## Frontend → Backend Contract

### Request
`POST /api/ai/insights`

```json
{
  "chartId": "daily-sales-trend",
  "chartType": "line",
  "selection": { 
    "point": { "x": "2024-05-01", "y": 40979.45, "label": "May 2024", "timestamp": "2024-05-01" },
    "range": { "start": "2024-05-01", "end": "2024-05-15" }
  },
  "aggregates": { "sum": 516840.33, "mean": 28713.35, "min": 4095.67, "max": 53583.71, "stddev": 10012.1, "pct_change": 120.0, "slope": 0.12 },
  "filters": { "category": ["Technology"], "region": ["West"], "currency": "USD", "unit": "USD" },
  "timeRange": { "from": "2023-01-01", "to": "2024-05-31" },
  "detailLevel": "short",
  "locale": "vi",
  "context": "So sánh với target Q1"
}
```

### Response
```json
{
  "id": "ins_123",
  "summary": "Tổng Sales tháng 10/2023 là 53.583 USD — cao nhất trong 17 tháng.",
  "highlights": [
    "Tăng 62% so với tháng trước (từ 25.292 USD lên 40.979 USD).",
    "Giảm mạnh ~90% trong 12/2023 so với trung bình.",
    "Xu hướng chung đang tăng nhẹ trong giai đoạn cuối."
  ],
  "explanations": [{ "text": "Pct change được tính từ điểm cuối và điểm liền trước trong chuỗi.", "metric_reference": "pct_change" }],
  "actions": ["Kiểm tra tồn kho cho category Technology", "Chạy chiến dịch khuyến mãi cho khu vực giảm mạnh"],
  "confidence": 0.78,
  "model_meta": { "model_name": "openrouter/...", "latency_ms": 4200 },
  "cached": false,
  "status": "succeeded"
}
```

If generation is slow, server may return:

```json
{ "id": "job_123", "status": "processing", "summary": "Insight đang được xử lý.", "highlights": [], "explanations": [], "actions": [], "confidence": 0, "model_meta": { "model_name": "pending", "latency_ms": 8000 }, "cached": false }
```

Then client polls `GET /api/ai/insights/{id}` until `status = succeeded`.

## Feedback
`POST /api/ai/insights/{id}/feedback`

```json
{ "useful": true, "comment": "Nêu đúng điểm tụt tháng 12." }
```

## Non-functional
- Cache TTL: 30 minutes (fingerprint of payload).
- Rate limit: configurable via `AI_INSIGHT_RATE_LIMIT`.
- Privacy: client should not send PII; server sanitizes common PII keys.
- Fallback: if model unavailable, return rule-based insight computed from aggregates.

