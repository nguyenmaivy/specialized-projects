import json
import urllib.request
import urllib.error

url = "http://localhost:8000/auth/login"
data = json.dumps({"username":"admin","password":"admin123"}).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        print("STATUS", resp.status)
        print(body)
except urllib.error.HTTPError as e:
    print("HTTPError", e.code)
    try:
        print(e.read().decode())
    except Exception:
        pass
except Exception as e:
    print("ERROR", str(e))
