import json
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("PORTFOLIO_DB", ROOT / "data" / "portfolio.db"))
MAX_BODY_SIZE = 16_384
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/script.js": ("script.js", "text/javascript; charset=utf-8"),
}


def initialize_database():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DATABASE)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS contact_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )


class PortfolioHandler(BaseHTTPRequestHandler):
    server_version = "PortfolioServer/1.0"

    def send_bytes(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; img-src 'self' data:; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_bytes(status, body, "application/json; charset=utf-8")

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == "/api/health":
            self.send_json(200, {"status": "ok"})
            return

        static_file = STATIC_FILES.get(route)
        if static_file is None:
            self.send_json(404, {"error": "Not found."})
            return

        filename, content_type = static_file
        try:
            body = (ROOT / filename).read_bytes()
        except OSError:
            self.send_json(500, {"error": "The requested page is unavailable."})
            return
        self.send_bytes(200, body, content_type)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/contact":
            self.send_json(404, {"error": "Not found."})
            return
        if self.headers.get_content_type() != "application/json":
            self.send_json(415, {"error": "Send the form as JSON."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid request size."})
            return
        if content_length <= 0 or content_length > MAX_BODY_SIZE:
            self.send_json(413, {"error": "The request is empty or too large."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "The request must contain valid JSON."})
            return
        if not isinstance(payload, dict):
            self.send_json(400, {"error": "Please provide a valid contact form."})
            return

        name = payload.get("name")
        email = payload.get("email")
        message = payload.get("message")
        if not all(isinstance(value, str) for value in (name, email, message)):
            self.send_json(400, {"error": "Name, email, and message are required."})
            return

        name, email, message = name.strip(), email.strip(), message.strip()
        if not name or len(name) > 100:
            self.send_json(400, {"error": "Name must be between 1 and 100 characters."})
            return
        if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
            self.send_json(400, {"error": "Please enter a valid email address."})
            return
        if len(message) < 10 or len(message) > 5000:
            self.send_json(400, {"error": "Message must be between 10 and 5,000 characters."})
            return

        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        try:
            with closing(sqlite3.connect(DATABASE, timeout=5)) as connection:
                with connection:
                    connection.execute(
                        "INSERT INTO contact_messages (name, email, message, created_at) VALUES (?, ?, ?, ?)",
                        (name, email, message, created_at),
                    )
        except sqlite3.Error:
            self.log_error("Unable to save contact message to the database")
            self.send_json(500, {"error": "Message could not be saved. Please try again later."})
            return

        self.send_json(201, {"message": "Thanks! Your message has been received."})

    def do_HEAD(self):
        self.send_error(405, "Method not allowed")

    def log_message(self, format_string, *args):
        super().log_message(format_string, *args)


if __name__ == "__main__":
    initialize_database()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), PortfolioHandler)
    print(f"Portfolio server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping portfolio server.")
    finally:
        server.server_close()
