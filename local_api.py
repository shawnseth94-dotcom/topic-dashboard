#!/usr/bin/env python3
"""
选题系统本地 API 服务
http://localhost:8888 → 看板（支持状态修改）
POST /update → 修改 .md 文件 frontmatter 字段
POST /delete → 真正删除 .md 文件
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import re
import os
import subprocess
import sys

TOPIC_DIR = "/Users/sethshang/Documents/草稿/选题库"
BUILD_SCRIPT = os.path.join(TOPIC_DIR, "build.py")
DIST_HTML = os.path.join(TOPIC_DIR, "dist", "index.html")
PORT = 8888

ALLOWED_FIELDS = {"状态", "优先级"}
ALLOWED_VALUES = {
    "状态": {"待执行", "写作中", "已发布", "搁置"},
    "优先级": {"高", "中", "低"},
}


def update_frontmatter(filepath, field, value):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = rf'^({re.escape(field)}:\s*).*$'
    new_content = re.sub(pattern, rf'\g<1>{value}', content, flags=re.MULTILINE)
    if new_content == content:
        return False, "未变化"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True, "ok"


def rebuild():
    subprocess.run([sys.executable, BUILD_SCRIPT], cwd=TOPIC_DIR, capture_output=True)


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            if os.path.exists(DIST_HTML):
                with open(DIST_HTML, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(404, "请先运行 build.py")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/update":
            self._handle_update()
        elif self.path == "/delete":
            self._handle_delete()
        else:
            self.send_error(404)

    def _handle_update(self):
        body = self._read_json()
        if body is None:
            return
        filename = body.get("filename", "")
        field = body.get("field", "")
        value = body.get("value", "")

        if not self._safe_fn(filename):
            return self._json(400, {"error": "非法文件名"})
        if field not in ALLOWED_FIELDS:
            return self._json(400, {"error": "不允许修改该字段"})
        if value not in ALLOWED_VALUES.get(field, set()):
            return self._json(400, {"error": "非法值"})

        filepath = os.path.join(TOPIC_DIR, filename)
        if not os.path.exists(filepath):
            return self._json(404, {"error": "文件不存在"})

        ok, msg = update_frontmatter(filepath, field, value)
        if ok:
            rebuild()
        self._json(200, {"ok": ok, "msg": msg})

    def _handle_delete(self):
        body = self._read_json()
        if body is None:
            return
        filename = body.get("filename", "")
        if not self._safe_fn(filename):
            return self._json(400, {"error": "非法文件名"})
        filepath = os.path.join(TOPIC_DIR, filename)
        if not os.path.exists(filepath):
            return self._json(404, {"error": "文件不存在"})
        os.remove(filepath)
        rebuild()
        self._json(200, {"ok": True})

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length))
        except Exception:
            self._json(400, {"error": "JSON解析失败"})
            return None

    def _safe_fn(self, fn):
        return bool(fn) and fn.endswith(".md") and "/" not in fn and "\\" not in fn

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[API] {fmt % args}")


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[选题看板] 本地访问: http://localhost:{PORT}")
    print(f"[选题看板] 选题目录: {TOPIC_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[选题看板] 已停止")
