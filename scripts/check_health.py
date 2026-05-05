import time
import requests
import json
import sys

URL = "http://localhost:8000/health"
for i in range(15):
    try:
        r = requests.get(URL, timeout=5)
        print('STATUS:', r.status_code)
        try:
            print(json.dumps(r.json(), ensure_ascii=False, indent=2))
        except Exception:
            print(r.text)
        sys.exit(0)
    except Exception as e:
        print(f'Attempt {i+1} failed:', e)
        time.sleep(1)
print('Health check failed after retries')
sys.exit(1)
