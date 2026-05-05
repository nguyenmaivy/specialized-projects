import urllib.request, json

for path in ['/', '/openapi.json', '/docs', '/redoc']:
    url = 'http://localhost:8000' + path
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            print(f"{path} -> {resp.status}")
            data = resp.read().decode('utf-8')
            if path == '/openapi.json':
                try:
                    o = json.loads(data)
                    print('Registered paths:')
                    for p in sorted(o.get('paths', {}).keys()):
                        print(' ', p)
                except Exception as e:
                    print('Failed to parse openapi.json:', e)
    except Exception as e:
        print(f"{path} -> ERROR: {e}")
