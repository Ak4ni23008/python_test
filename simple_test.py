"""
Railway smoke test — replace this file with your real trading code later.

- Prints 1 to 10 in deploy logs
- Serves the same numbers in the browser (Railway needs a web server on $PORT)
"""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def print_numbers() -> str:
    """Print and return numbers 1 through 10."""
    lines: list[str] = []
    for i in range(1, 11):
        print(i, flush=True)
        lines.append(str(i))
    return "\n".join(lines)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = "Numbers 1 to 10:\n\n" + print_numbers()
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:
        pass  # keep Railway logs clean


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Server starting on port {port}", flush=True)
    print_numbers()
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Open your Railway URL to see numbers 1-10", flush=True)
    server.serve_forever()
