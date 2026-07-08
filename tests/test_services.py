from __future__ import annotations

import json
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
        self.deepseek_requests: list[dict[str, object]] = []

        def fake_deepseek_post(
            url: str,
            headers: dict[str, str],
            payload: dict[str, object],
            timeout: float,
        ) -> dict[str, object]:
            self.deepseek_requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            messages = payload.get("messages", [])
            user_message = messages[-1]["content"] if isinstance(messages, list) and messages else ""
            if user_message == "连接测试":
                content = {"ok": True, "message": "connected"}
            elif "本地规则兜底" in str(user_message):
                content = {"action": "set_device", "device_id": 7, "status": "broken", "reply": "无效状态"}
            elif "客厅亮" in str(user_message):
                content = {"action": "set_device", "device_id": 7, "status": "on", "reply": "已打开客厅灯。"}
            else:
                content = {"action": "none", "reply": "无法识别"}
            return {"choices": [{"message": {"content": json.dumps(content, ensure_ascii=False)}}]}

        self.config_path = Path(self.temp_dir.name) / "deepseek_config.json"
        self.service = SmartHomeService(
            self.db,
            self.auth,
            llm_config_path=self.config_path,
            deepseek_http_post=fake_deepseek_post,
        )
        self.admin = self.auth.login("admin", "Admin@SE2026!")["user"]
        self.member = self.auth.login("member", "Member@SE2026!")["user"]
        self.guest = self.auth.login("guest", "Guest@SE2026!")["user"]

    def tearDown(self) -> None:
        self.db.close()
        self.temp_dir.cleanup()

    def test_login_rejects_wrong_password(self) -> None:
        with self.assertRaises(AuthError):
            self.auth.login("admin", "wrong")

    def test_guest_cannot_control_device(self) -> None:
        with self.assertRaises(PermissionError):
            self.service.set_device_status(self.guest, 7, "on")

    def test_invalid_device_status_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.service.set_device_status(self.member, 7, "broken")

    def test_voice_command_turns_on_living_room_light(self) -> None:
        result = self.service.handle_voice_command(self.member, "打开客厅灯")
        self.assertEqual(result["type"], "device")
        device = self.service.device(7)
        self.assertEqual(device["status"], "on")

    def test_voice_command_opens_lock_as_unlock(self) -> None:
        result = self.service.handle_voice_command(self.member, "打开门锁")
        self.assertEqual(result["type"], "device")
        self.assertEqual(result["device"]["id"], 4)
        self.assertEqual(result["device"]["status"], "unlocked")

    def test_voice_command_closes_camera_to_privacy(self) -> None:
        result = self.service.handle_voice_command(self.member, "关闭客厅摄像头")
        self.assertEqual(result["type"], "device")
        self.assertEqual(result["device"]["id"], 2)
        self.assertEqual(result["device"]["status"], "privacy")

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
        self.assertNotIn("玄关玄关", recordings[0]["title"])
        self.assertNotIn("玄关", recordings[0]["title"])

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
        self.assertEqual(self.service.device(9)["status"], "standby")

    def test_resolve_alert_keeps_alarm_active_when_other_alerts_are_open(self) -> None:
        first = self.service.simulate_alert(self.member, "smoke", 4)
        second = self.service.simulate_alert(self.member, "intrusion", 1)

        self.service.resolve_alert(self.member, first["id"], "厨房烟雾已排查。")
        self.assertEqual(self.service.device(9)["status"], "active")

        self.service.resolve_alert(self.member, second["id"], "玄关入侵已排查。")
        self.assertEqual(self.service.device(9)["status"], "standby")

    def test_deepseek_config_is_saved_locally_without_exposing_secret(self) -> None:
        api_key = "sk-test-1234567890"
        config = self.service.save_deepseek_config(self.admin, api_key)

        self.assertTrue(self.config_path.exists())
        self.assertIn(api_key, self.config_path.read_text(encoding="utf-8"))
        self.assertTrue(config["hasApiKey"])
        self.assertNotEqual(config["maskedApiKey"], api_key)
        self.assertNotIn(api_key, json.dumps(config, ensure_ascii=False))

    def test_deepseek_connection_uses_saved_key(self) -> None:
        self.service.save_deepseek_config(self.admin, "sk-test-1234567890")

        result = self.service.test_deepseek_connection(self.member)

        self.assertTrue(result["ok"])
        self.assertEqual(self.deepseek_requests[-1]["headers"]["Authorization"], "Bearer sk-test-1234567890")

    def test_deepseek_voice_command_controls_device(self) -> None:
        self.service.save_deepseek_config(self.admin, "sk-test-1234567890")

        result = self.service.handle_voice_command(self.member, "帮我把客厅亮一点")

        self.assertEqual(result["source"], "deepseek")
        self.assertEqual(result["type"], "device")
        self.assertEqual(self.service.device(7)["status"], "on")

    def test_deepseek_voice_falls_back_to_local_rules(self) -> None:
        self.service.save_deepseek_config(self.admin, "sk-test-1234567890")

        result = self.service.handle_voice_command(self.member, "本地规则兜底，打开客厅灯")

        self.assertEqual(result["source"], "local")
        self.assertEqual(result["type"], "device")
        self.assertEqual(self.service.device(7)["status"], "on")


if __name__ == "__main__":
    unittest.main()
