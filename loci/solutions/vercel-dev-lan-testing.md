# Vercel Dev: LAN Testing from Phone

`vercel dev` only binds to `localhost` — no `--listen 0.0.0.0` support. To test from a phone on the same Wi-Fi:

## Python TCP Forwarder

```bash
python3 -c "
import socket, threading
def forward(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data: break
            dst.sendall(data)
    except: pass
    finally: src.close(); dst.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 3457))
s.listen(5)
while True:
    c, _ = s.accept()
    r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    r.connect(('127.0.0.1', 3456))
    threading.Thread(target=forward, args=(c, r), daemon=True).start()
    threading.Thread(target=forward, args=(r, c), daemon=True).start()
" &
```

Then access `http://<local-ip>:3457` from phone. Get IP with `ifconfig | grep "inet " | grep -v 127.0.0.1`.

## Alternative

Install `socat` (`brew install socat`):
```bash
socat TCP-LISTEN:3457,fork,bind=0.0.0.0 TCP:localhost:3456
```
