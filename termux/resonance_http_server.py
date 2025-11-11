#!/usr/bin/env python3
"""
Resonance HTTP API Server
Provides HTTP access to resonance.sqlite3 for cross-app communication
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Configuration
DB_PATH = Path.home() / "ariannamethod" / "resonance.sqlite3"
LOG_DIR = Path.home() / "ariannamethod" / "logs"
LOG_FILE = LOG_DIR / "resonance_api.log"
PORT = 8080
HOST = "localhost"

# Setup logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ResonanceAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler for resonance.sqlite3 API"""

    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info("%s - %s" % (self.address_string(), format % args))

    def _send_json(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _send_error_json(self, message, status=400):
        """Send JSON error"""
        self._send_json({"error": message, "status": "error"}, status)

    def _get_db(self):
        """Get database connection"""
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found: {DB_PATH}")
        return sqlite3.connect(str(DB_PATH))

    def do_GET(self):
        """Handle GET requests"""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        try:
            if path == "/health":
                self._handle_health()
            elif path == "/resonance/recent":
                limit = int(params.get('limit', [100])[0])
                self._handle_recent(limit)
            elif path == "/resonance/since":
                timestamp = params.get('timestamp', [None])[0]
                if not timestamp:
                    self._send_error_json("Missing timestamp parameter")
                    return
                self._handle_since(timestamp)
            else:
                self._send_error_json(f"Unknown endpoint: {path}", 404)
        except Exception as e:
            logger.error(f"GET {path} error: {e}")
            self._send_error_json(str(e), 500)

    def do_POST(self):
        """Handle POST requests"""
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            if path == "/resonance/write":
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                self._handle_write(data)
            else:
                self._send_error_json(f"Unknown endpoint: {path}", 404)
        except Exception as e:
            logger.error(f"POST {path} error: {e}")
            self._send_error_json(str(e), 500)

    def _handle_health(self):
        """Health check endpoint"""
        try:
            conn = self._get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM resonance_notes")
            note_count = cursor.fetchone()[0]
            conn.close()

            db_size = DB_PATH.stat().st_size
            db_size_mb = db_size / (1024 * 1024)

            self._send_json({
                "status": "ok",
                "db_path": str(DB_PATH),
                "db_size_bytes": db_size,
                "db_size_mb": round(db_size_mb, 2),
                "note_count": note_count,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            self._send_error_json(f"Health check failed: {e}", 500)

    def _handle_recent(self, limit):
        """Get recent notes"""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, content, context, source
            FROM resonance_notes
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        notes = []
        for row in cursor.fetchall():
            notes.append({
                "timestamp": row[0],
                "content": row[1],
                "context": row[2],
                "source": row[3]
            })

        conn.close()

        self._send_json({
            "status": "ok",
            "count": len(notes),
            "limit": limit,
            "notes": notes
        })

    def _handle_since(self, timestamp):
        """Get notes since timestamp"""
        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, content, context, source
            FROM resonance_notes
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        """, (timestamp,))

        notes = []
        for row in cursor.fetchall():
            notes.append({
                "timestamp": row[0],
                "content": row[1],
                "context": row[2],
                "source": row[3]
            })

        conn.close()

        self._send_json({
            "status": "ok",
            "since": timestamp,
            "count": len(notes),
            "notes": notes
        })

    def _handle_write(self, data):
        """Write new note to resonance"""
        required = ["content", "source"]
        for field in required:
            if field not in data:
                self._send_error_json(f"Missing required field: {field}")
                return

        content = data["content"]
        source = data["source"]
        context = data.get("context", "")
        timestamp = data.get("timestamp", datetime.now().isoformat())

        conn = self._get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resonance_notes (timestamp, content, context, source)
            VALUES (?, ?, ?, ?)
        """, (timestamp, content, context, source))
        conn.commit()
        conn.close()

        logger.info(f"Written note from {source}: {content[:100]}...")

        self._send_json({
            "status": "ok",
            "message": "Note written successfully",
            "timestamp": timestamp,
            "source": source
        })


def main():
    """Start HTTP server"""
    if not DB_PATH.exists():
        logger.error(f"Database not found: {DB_PATH}")
        sys.exit(1)

    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, ResonanceAPIHandler)

    logger.info("=" * 60)
    logger.info("Resonance HTTP API Server Starting")
    logger.info("=" * 60)
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Listening: http://{HOST}:{PORT}")
    logger.info(f"Logs: {LOG_FILE}")
    logger.info("")
    logger.info("Endpoints:")
    logger.info(f"  GET  /health")
    logger.info(f"  GET  /resonance/recent?limit=N")
    logger.info(f"  GET  /resonance/since?timestamp=YYYY-MM-DD HH:MM:SS")
    logger.info(f"  POST /resonance/write")
    logger.info("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.shutdown()


if __name__ == "__main__":
    main()
