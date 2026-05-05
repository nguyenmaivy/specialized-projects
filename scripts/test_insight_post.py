import json
import requests

payload = {
    "chartId": "daily-sales-trend",
    "chartType": "line",
    "filters": {
        "category": ["Office Supplies"],
        "region": ["Central"],
        "start_date": "2014-01-03",
        "end_date": "2016-06-30"
    },
    "detailLevel": "short",
    "locale": "vi"
}

try:
    r = requests.post("http://localhost:8000/api/ai/insights", json=payload, timeout=30)
    print("STATUS:", r.status_code)
    try:
        print(json.dumps(r.json(), ensure_ascii=False, indent=2))
    except Exception:
        print(r.text)
except Exception as e:
    print('Request failed:', e)
