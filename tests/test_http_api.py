from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from smart_home.auth import AuthService
from smart_home.database import Database
from smart_home.server import create_handler
from smart_home.services import SmartHomeService


class SmartHomeHttpApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "api-test.sqlite")
        self.db.init_schema()
        self.db.seed()
        self.auth = AuthService(self.db)
        self.service = SmartHomeService(self.db, self.auth)
        handler = create_handler(self.service, self.auth, PROJECT_ROOT / "src" / "web")
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.db.close()
        self.temp_dir.cleanup()

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, object] | None = None,
        token: str | None = None,
    ) -> tuple[int, dict[str, object]]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(body or {}, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = Request(f"{self.base_url}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8") or "{}")
                return response.status, payload
        except HTTPError as error:
            payload = json.loads(error.read().decode("utf-8") or "{}")
            return error.code, payload

    def login(self, username: str = "admin", password: str = "Admin@SE2026!") -> str:
        status, payload = self.request(
            "POST",
            "/api/login",
            {"username": username, "password": password},
        )
        self.assertEqual(status, 200)
        return str(payload["token"])

    def test_login_success_returns_token_and_admin_user(self) -> None:
        status, payload = self.request(
            "POST",
            "/api/login",
            {"username": "admin", "password": "Admin@SE2026!"},
        )

        self.assertEqual(status, 200)
        self.assertIn("token", payload)
        self.assertEqual(payload["user"]["role"], "admin")

    def test_dashboard_requires_login(self) -> None:
        status, payload = self.request("GET", "/api/dashboard")

        self.assertEqual(status, 401)
        self.assertIn("请先登录", str(payload["error"]))

    def test_admin_dashboard_returns_seeded_counts(self) -> None:
        token = self.login()

        status, payload = self.request("GET", "/api/dashboard", token=token)

        self.assertEqual(status, 200)
        self.assertEqual(payload["stats"]["roomCount"], 5)
        self.assertEqual(payload["stats"]["deviceCount"], 9)
        self.assertEqual(payload["stats"]["cameraCount"], 3)
        self.assertEqual(payload["user"]["username"], "admin")

    def test_guest_cannot_patch_device_status(self) -> None:
        guest_token = self.login("guest", "Guest@SE2026!")

        status, payload = self.request(
            "PATCH",
            "/api/devices/7",
            {"status": "on"},
            token=guest_token,
        )

        self.assertEqual(status, 403)
        self.assertIn("权限", str(payload["error"]))

    def test_guest_cannot_simulate_alert(self) -> None:
        guest_token = self.login("guest", "Guest@SE2026!")

        status, payload = self.request(
            "POST",
            "/api/alerts/simulate",
            {"event_type": "intrusion", "room_id": 1},
            token=guest_token,
        )

        self.assertEqual(status, 403)
        self.assertIn("权限", str(payload["error"]))

    def test_member_cannot_read_admin_logs(self) -> None:
        member_token = self.login("member", "Member@SE2026!")

        status, payload = self.request("GET", "/api/logs", token=member_token)

        self.assertEqual(status, 403)
        self.assertIn("权限", str(payload["error"]))

    def test_login_rejects_sql_injection_like_username(self) -> None:
        status, payload = self.request(
            "POST",
            "/api/login",
            {"username": "admin' OR '1'='1", "password": "anything"},
        )

        self.assertEqual(status, 401)
        self.assertIn("用户名或密码错误", str(payload["error"]))

    def test_recording_search_handles_xss_like_keyword(self) -> None:
        token = self.login()
        keyword = quote("<script>alert(1)</script>")

        status, payload = self.request("GET", f"/api/recordings?keyword={keyword}", token=token)

        self.assertEqual(status, 200)
        self.assertIn("recordings", payload)

    def test_dashboard_response_time_under_two_seconds(self) -> None:
        token = self.login()

        started = time.perf_counter()
        status, payload = self.request("GET", "/api/dashboard", token=token)
        elapsed = time.perf_counter() - started

        self.assertEqual(status, 200)
        self.assertEqual(payload["stats"]["roomCount"], 5)
        self.assertLess(elapsed, 2.0)


if __name__ == "__main__":
    unittest.main()
