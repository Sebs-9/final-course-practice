from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from smart_home.auth import AuthError, AuthService
from smart_home.database import Database
from smart_home.services import SmartHomeService


class SmartHomeServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp_dir.name) / "test.sqlite")
        self.db.init_schema()
        self.db.seed()
        self.auth = AuthService(self.db)
        self.service = SmartHomeService(self.db, self.auth)
        self.admin = self.auth.login("admin", "admin123")["user"]
        self.member = self.auth.login("member", "member123")["user"]
        self.guest = self.auth.login("guest", "guest123")["user"]

    def tearDown(self) -> None:
        self.db.close()
        self.temp_dir.cleanup()

    def test_login_rejects_wrong_password(self) -> None:
        with self.assertRaises(AuthError):
            self.auth.login("admin", "wrong")

    def test_guest_cannot_control_device(self) -> None:
        with self.assertRaises(PermissionError):
            self.service.set_device_status(self.guest, 7, "on")

    def test_voice_command_turns_on_living_room_light(self) -> None:
        result = self.service.handle_voice_command(self.member, "打开客厅灯")
        self.assertEqual(result["type"], "device")
        device = self.service.device(7)
        self.assertEqual(device["status"], "on")

    def test_voice_command_queries_camera_without_changing_status(self) -> None:
        before = self.service.device(2)["status"]
        result = self.service.handle_voice_command(self.member, "查看客厅摄像头")
        after = self.service.device(2)["status"]
        self.assertEqual(result["type"], "camera")
        self.assertEqual(before, after)

    def test_simulate_alert_creates_recording_and_linkage(self) -> None:
        alert = self.service.simulate_alert(self.admin, "intrusion", 1)
        self.assertEqual(alert["event_type"], "intrusion")
        self.assertEqual(alert["status"], "open")
        alarm = self.service.device(9)
        self.assertEqual(alarm["status"], "active")
        recordings = self.service.recordings(event_type="intrusion")
        self.assertGreaterEqual(len(recordings), 1)

    def test_recording_filter_by_keyword(self) -> None:
        records = self.service.recordings(keyword="厨房")
        self.assertTrue(any("厨房" in item["title"] or "厨房" in item["summary"] for item in records))

    def test_scene_activation_updates_devices(self) -> None:
        scene = self.service.activate_scene(self.member, 1)
        self.assertEqual(scene["name"], "离家安防")
        lock = self.service.device(4)
        light = self.service.device(7)
        self.assertEqual(lock["status"], "locked")
        self.assertEqual(light["status"], "off")

    def test_resolve_alert_updates_status(self) -> None:
        alert = self.service.simulate_alert(self.member, "smoke", 4)
        resolved = self.service.resolve_alert(self.member, alert["id"], "已通知家人并检查厨房。")
        self.assertEqual(resolved["status"], "resolved")
        self.assertIn("厨房", resolved["resolution_note"])


if __name__ == "__main__":
    unittest.main()
