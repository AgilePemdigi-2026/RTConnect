import http.server
import socketserver
import urllib.request
import urllib.error
import sys

FRONTEND_URL = "http://127.0.0.1:3000"
BACKEND_URL = "http://127.0.0.1:5000"
PROXY_PORT = 8080

class DevProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self._proxy()

    def do_POST(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy()

    def do_OPTIONS(self):
        self._proxy()

    def do_HEAD(self):
        self._proxy()

    def _proxy(self):
        if self.path.startswith("/api/"):
            target_url = f"{BACKEND_URL}{self.path}"
        else:
            target_url = f"{FRONTEND_URL}{self.path}"

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req_headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ["host", "content-length"]:
                req_headers[k] = v

        req = urllib.request.Request(
            target_url,
            data=body,
            headers=req_headers,
            method=self.command,
        )

        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for header, val in resp.getheaders():
                    # Strip hop-by-hop headers
                    if header.lower() not in ["transfer-encoding", "content-length"]:
                        self.send_header(header, val)
                response_body = resp.read()
                self.send_header("Content-Length", str(len(response_body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(response_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for header, val in e.headers.items():
                if header.lower() not in ["transfer-encoding", "content-length"]:
                    self.send_header(header, val)
            err_body = e.read()
            self.send_header("Content-Length", str(len(err_body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Proxy Error: {e}".encode())

def run():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PROXY_PORT), DevProxyHandler) as httpd:
        print(f"[*] Dev Proxy running on port {PROXY_PORT}")
        sys.stdout.flush()
        httpd.serve_forever()

if __name__ == "__main__":
    run()
