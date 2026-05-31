from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .auth import AuthError, AuthService
from .database import Database
from .services import SmartHomeService


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def create_handler(service: SmartHomeService, auth: AuthService, static_dir: Path):
    class SmartHomeHandler(BaseHTTPRequestHandler):
        server_version = "SmartHomeSE/1.0"

        def do_GET(self) -> None:
            self._dispatch("GET")

        def do_POST(self) -> None:
            self._dispatch("POST")

        def do_PATCH(self) -> None:
            self._dispatch("PATCH")

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _dispatch(self, method: str) -> None:
            try:
                parsed = urlparse(self.path)
                if parsed.path.startswith("/api/") or parsed.path == "/health":
                    payload = self._handle_api(method, parsed.path, parse_qs(parsed.query))
                    self._send_json(payload)
                else:
                    self._serve_static(parsed.path)
            except ApiError as exc:
                self._send_json({"error": exc.message}, status=exc.status)
            except AuthError as exc:
                self._send_json({"error": str(exc)}, status=401)
            except PermissionError as exc:
                self._send_json({"error": str(exc)}, status=403)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
            except Exception as exc:
                self._send_json({"error": f"服务器内部错误：{exc}"}, status=500)

        def _handle_api(self, method: str, path: str, query: dict[str, list[str]]) -> dict[str, Any]:
            if path == "/health":
                return {"status": "ok"}
            if path == "/api/login" and method == "POST":
                body = self._read_json()
                return auth.login(body.get("username", ""), body.get("password", ""))

            user = self._current_user()
            parts = [part for part in path.split("/") if part]

            if path == "/api/session" and method == "GET":
                return {"user": user}
            if path == "/api/dashboard" and method == "GET":
                return service.dashboard(user)
            if path == "/api/devices" and method == "GET":
                return {"devices": service.devices()}
            if len(parts) == 3 and parts[:2] == ["api", "devices"] and method == "PATCH":
                body = self._read_json()
                return {"device": service.set_device_status(user, int(parts[2]), body.get("status", ""))}
            if path == "/api/alerts" and method == "GET":
                status = self._first(query, "status")
                return {"alerts": service.alerts(status=status)}
            if path == "/api/alerts/simulate" and method == "POST":
                body = self._read_json()
                return {"alert": service.simulate_alert(user, body.get("event_type", "motion"), int(body.get("room_id", 1)))}
            if len(parts) == 4 and parts[:2] == ["api", "alerts"] and parts[3] == "resolve" and method == "POST":
                body = self._read_json()
                return {"alert": service.resolve_alert(user, int(parts[2]), body.get("note", ""))}
            if path == "/api/recordings" and method == "GET":
                room = self._first(query, "room_id")
                return {
                    "recordings": service.recordings(
                        room_id=int(room) if room else None,
                        event_type=self._first(query, "event_type"),
                        keyword=self._first(query, "keyword"),
                    )
                }
            if path == "/api/voice" and method == "POST":
                body = self._read_json()
                return {"result": service.handle_voice_command(user, body.get("command", ""))}
            if path == "/api/scenes" and method == "GET":
                return {"scenes": service.scenes()}
            if len(parts) == 4 and parts[:2] == ["api", "scenes"] and parts[3] == "activate" and method == "POST":
                return {"scene": service.activate_scene(user, int(parts[2]))}
            if path == "/api/logs" and method == "GET":
                auth.require(user, {"admin"})
                return {"logs": service.logs()}

            raise ApiError(404, "接口不存在。")

        def _current_user(self) -> dict[str, Any]:
            header = self.headers.get("Authorization", "")
            token = header.replace("Bearer ", "", 1).strip() if header.startswith("Bearer ") else ""
            return auth.get_user(token)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw or "{}")

        def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _serve_static(self, request_path: str) -> None:
            relative = "index.html" if request_path in {"/", ""} else request_path.lstrip("/")
            target = (static_dir / relative).resolve()
            if not str(target).startswith(str(static_dir.resolve())) or not target.exists() or target.is_dir():
                raise ApiError(404, "静态文件不存在。")
            data = target.read_bytes()
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
                content_type = f"{content_type}; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        @staticmethod
        def _first(query: dict[str, list[str]], key: str) -> str | None:
            value = query.get(key)
            return value[0] if value else None

    return SmartHomeHandler


def run_server(host: str, port: int, db_path: Path, static_dir: Path) -> None:
    db = Database(db_path)
    db.init_schema()
    db.seed()
    auth = AuthService(db)
    service = SmartHomeService(db, auth)
    handler = create_handler(service, auth, static_dir)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"Smart home prototype running at http://{host}:{port}")
    print("Demo users: admin/admin123, member/member123, guest/guest123")
    try:
        httpd.serve_forever()
    finally:
        db.close()
