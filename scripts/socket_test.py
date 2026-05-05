import socket

try:
    s = socket.create_connection(('localhost', 8000), timeout=5)
    s.sendall(b'GET /health HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
    data = b''
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
    print(data.decode('utf-8', errors='replace'))
    s.close()
except Exception as e:
    print('socket error:', e)
