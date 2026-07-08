from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .auth import AuthService
from .database import Database, utc_now
from .deepseek import DeepSeekClient, DeepSeekConfigStore, HttpPost


DEVICE_STATUS_OPTIONS: dict[str, set[str]] = {
    "light": {"on", "off"},
    "climate": {"cooling", "off"},
    "camera": {"active", "privacy"},
    "alarm": {"active", "standby"},
    "lock": {"locked", "unlocked"},
    "sensor": {"armed", "normal"},
}

ALERT_EVENT_TYPES = {"intrusion", "smoke", "fall", "door_open", "motion"}


class SmartHomeService:
    def __init__(
        self,
        db: Database,
        auth: AuthService,
        llm_config_path: str | Path | None = None,
        deepseek_http_post: HttpPost | None = None,
    ):
        self.db = db
        self.auth = auth
        config_path = Path(llm_config_path) if llm_config_path else self._default_deepseek_config_path()
        self.deepseek_store = DeepSeekConfigStore(config_path)
        self.deepseek = DeepSeekClient(self.deepseek_store, deepseek_http_post)

    def _default_deepseek_config_path(self) -> Path:
        if self.db.path == ":memory:":
            return Path("data") / "deepseek_config.json"
        return Path(self.db.path).with_name("deepseek_config.json")

    def dashboard(self, user: dict[str, Any]) -> dict[str, Any]:
        rooms = self.rooms()
        devices = self.devices()
        alerts = self.alerts(status="open")
        recordings = self.recordings(limit=5)
        scenes = self.scenes()
        logs = self.logs(limit=8) if user["role"] == "admin" else []
        stats = {
            "roomCount": len(rooms),
            "deviceCount": len(devices),
            "onlineCount": sum(1 for device in devices if device["online"]),
            "openAlertCount": len(alerts),
            "cameraCount": sum(1 for device in devices if device["type"] == "camera"),
        }
        return {
            "user": user,
            "stats": stats,
            "rooms": rooms,
            "devices": devices,
            "alerts": alerts,
            "recordings": recordings,
            "scenes": scenes,
            "logs": logs,
            "deepseek": self.deepseek_config(user),
        }

    def rooms(self) -> list[dict[str, Any]]:
        return self.db.query_all("SELECT * FROM rooms ORDER BY id")

    def devices(self) -> list[dict[str, Any]]:
        rows = self.db.query_all(
            """
            SELECT d.*, r.name AS room_name
            FROM devices d
            JOIN rooms r ON r.id = d.room_id
            ORDER BY d.room_id, d.id
            """
        )
        for row in rows:
            row["online"] = bool(row["online"])
            row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
        return rows

    def scenes(self) -> list[dict[str, Any]]:
        rows = self.db.query_all("SELECT * FROM scenes ORDER BY id")
        for row in rows:
            row["is_active"] = bool(row["is_active"])
        return rows

    def alerts(self, status: str | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        params: list[Any] = []
        where = ""
        if status:
            where = "WHERE a.status = ?"
            params.append(status)
        sql = f"""
            SELECT a.*, r.name AS room_name, d.name AS device_name
            FROM alerts a
            JOIN rooms r ON r.id = a.room_id
            LEFT JOIN devices d ON d.id = a.device_id
            {where}
            ORDER BY a.triggered_at DESC, a.id DESC
        """
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        return self.db.query_all(sql, params)

    def recordings(
        self,
        room_id: int | None = None,
        event_type: str | None = None,
        keyword: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses = []
        params: list[Any] = []
        if room_id:
            clauses.append("rec.room_id = ?")
            params.append(room_id)
        if event_type:
            clauses.append("rec.event_type = ?")
            params.append(event_type)
        if keyword:
            clauses.append("(rec.title LIKE ? OR rec.summary LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"""
            SELECT rec.*, r.name AS room_name, d.name AS camera_name
            FROM recordings rec
            JOIN rooms r ON r.id = rec.room_id
            JOIN devices d ON d.id = rec.camera_device_id
            {where}
            ORDER BY rec.started_at DESC, rec.id DESC
        """
        if limit:
            sql += " LIMIT ?"
            params.append(limit)
        return self.db.query_all(sql, params)

    def set_device_status(self, user: dict[str, Any], device_id: int, status: str) -> dict[str, Any]:
        self.auth.require(user, {"admin", "member"})
        status = (status or "").strip()
        if not status:
            raise ValueError("设备状态不能为空。")
        device = self.db.query_one("SELECT * FROM devices WHERE id = ?", (device_id,))
        if not device:
            raise ValueError("设备不存在。")
        allowed_statuses = DEVICE_STATUS_OPTIONS.get(device["type"], set())
        if allowed_statuses and status not in allowed_statuses:
            allowed_text = "、".join(sorted(allowed_statuses))
            raise ValueError(f"{device['name']} 不支持状态 {status}，可用状态：{allowed_text}。")
        now = utc_now()
        self.db.execute(
            "UPDATE devices SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, device_id),
        )
        self.log(user, "set_device_status", "device", device_id, f"{device['name']} 状态变更为 {status}")
        return self.device(device_id)

    def device(self, device_id: int) -> dict[str, Any]:
        rows = [device for device in self.devices() if device["id"] == device_id]
        if not rows:
            raise ValueError("设备不存在。")
        return rows[0]

    def simulate_alert(self, user: dict[str, Any], event_type: str, room_id: int) -> dict[str, Any]:
        self.auth.require(user, {"admin", "member"})
        event_type = (event_type or "").strip()
        if event_type not in ALERT_EVENT_TYPES:
            raise ValueError("告警事件类型不支持。")
        room = self.db.query_one("SELECT * FROM rooms WHERE id = ?", (room_id,))
        if not room:
            raise ValueError("房间不存在。")
        severity_map = {
            "intrusion": "high",
            "smoke": "critical",
            "fall": "critical",
            "door_open": "medium",
            "motion": "low",
        }
        message_map = {
            "intrusion": f"{room['name']} 检测到疑似陌生人闯入。",
            "smoke": f"{room['name']} 烟雾浓度异常，请立即检查。",
            "fall": f"{room['name']} 检测到疑似跌倒事件。",
            "door_open": f"{room['name']} 门窗传感器异常开启。",
            "motion": f"{room['name']} 检测到移动目标。",
        }
        recording_title_map = {
            "intrusion": "疑似陌生人闯入片段",
            "smoke": "烟雾异常片段",
            "fall": "疑似跌倒片段",
            "door_open": "门窗异常片段",
            "motion": "移动检测片段",
        }
        severity = severity_map.get(event_type, "medium")
        message = message_map.get(event_type, f"{room['name']} 出现 {event_type} 事件。")
        device = self._best_device_for_event(room_id, event_type)
        now = utc_now()
        alert_id = self.db.execute(
            """
            INSERT INTO alerts(room_id, device_id, event_type, severity, status, message, triggered_at)
            VALUES (?, ?, ?, ?, 'open', ?, ?)
            """,
            (room_id, device["id"] if device else None, event_type, severity, message, now),
        ).lastrowid
        camera = self._camera_for_room(room_id)
        if camera:
            self.db.execute(
                """
                INSERT INTO recordings(room_id, camera_device_id, title, event_type, started_at, duration_seconds, storage_path, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    room_id,
                    camera["id"],
                    recording_title_map.get(event_type, f"{event_type} 事件片段"),
                    event_type,
                    now,
                    60,
                    f"/recordings/{event_type}-{alert_id}.mp4",
                    message,
                ),
            )
        self._apply_emergency_linkage(room_id, event_type)
        self.log(user, "simulate_alert", "alert", alert_id, message)
        return self.alerts(limit=1)[0]

    def resolve_alert(self, user: dict[str, Any], alert_id: int, note: str) -> dict[str, Any]:
        self.auth.require(user, {"admin", "member"})
        alert = self.db.query_one("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        if not alert:
            raise ValueError("告警不存在。")
        now = utc_now()
        self.db.execute(
            """
            UPDATE alerts
            SET status = 'resolved', resolved_at = ?, resolution_note = ?
            WHERE id = ?
            """,
            (now, note or "已确认并处理。", alert_id),
        )
        self.log(user, "resolve_alert", "alert", alert_id, note or "已确认并处理。")
        return self.db.query_one("SELECT * FROM alerts WHERE id = ?", (alert_id,)) or {}

    def activate_scene(self, user: dict[str, Any], scene_id: int) -> dict[str, Any]:
        self.auth.require(user, {"admin", "member"})
        scene = self.db.query_one("SELECT * FROM scenes WHERE id = ?", (scene_id,))
        if not scene:
            raise ValueError("场景不存在。")
        now = utc_now()
        actions = self.db.query_all("SELECT * FROM scene_actions WHERE scene_id = ?", (scene_id,))
        for action in actions:
            self.db.execute(
                "UPDATE devices SET status = ?, updated_at = ? WHERE id = ?",
                (action["target_status"], now, action["device_id"]),
            )
        self.db.execute("UPDATE scenes SET is_active = 0")
        self.db.execute("UPDATE scenes SET is_active = 1 WHERE id = ?", (scene_id,))
        self.log(user, "activate_scene", "scene", scene_id, f"启动场景：{scene['name']}")
        updated = self.db.query_one("SELECT * FROM scenes WHERE id = ?", (scene_id,)) or {}
        updated["is_active"] = bool(updated["is_active"])
        return updated

    def handle_voice_command(self, user: dict[str, Any], command: str) -> dict[str, Any]:
        self.auth.require(user, {"admin", "member"})
        command = (command or "").strip()
        if not command:
            raise ValueError("语音指令不能为空。")

        if self.deepseek_store.load().has_api_key:
            try:
                intent = self.deepseek.parse_voice_command(
                    command=command,
                    rooms=self.rooms(),
                    devices=self.devices(),
                    scenes=self.scenes(),
                    status_options=DEVICE_STATUS_OPTIONS,
                    event_types=ALERT_EVENT_TYPES,
                )
                return self._execute_deepseek_intent(user, command, intent)
            except ValueError as exc:
                try:
                    result = self._handle_rule_voice_command(user, command)
                except ValueError as rule_exc:
                    raise ValueError(f"DeepSeek 未能解析该指令：{exc}") from rule_exc
                result["source"] = "local"
                result["llm_error"] = str(exc)
                result["message"] = f"{result['message']}（DeepSeek 未完成解析，已使用本地规则。）"
                return result

        return self._handle_rule_voice_command(user, command)

    def _handle_rule_voice_command(self, user: dict[str, Any], command: str) -> dict[str, Any]:
        scene = self._scene_from_command(command)
        if scene:
            updated = self.activate_scene(user, scene["id"])
            return {"type": "scene", "message": f"已启动{updated['name']}。", "scene": updated, "source": "local"}

        alert_event = self._event_from_command(command)
        if alert_event:
            room_id = self._room_from_command(command) or 1
            alert = self.simulate_alert(user, alert_event, room_id)
            return {"type": "alert", "message": alert["message"], "alert": alert, "source": "local"}

        camera = self._camera_query_from_command(command)
        if camera:
            self.log(user, "voice_query_camera", "device", camera["id"], command)
            return {"type": "camera", "message": f"正在查看{camera['name']}。", "device": camera, "source": "local"}

        device_match = self._device_from_command(command)
        if device_match:
            status = self._status_from_command(command, device_match["type"])
            device = self.set_device_status(user, device_match["id"], status)
            return {"type": "device", "message": f"{device['name']} 已切换为 {device['status']}。", "device": device, "source": "local"}

        raise ValueError("未能识别该语音指令，请尝试：打开客厅灯、启动离家安防、模拟厨房烟雾。")

    def _execute_deepseek_intent(
        self,
        user: dict[str, Any],
        command: str,
        intent: dict[str, Any],
    ) -> dict[str, Any]:
        action = str(intent.get("action") or "none").strip()
        reply = str(intent.get("reply") or "").strip()

        if action == "set_device":
            device_id = self._intent_int(intent, "device_id")
            status = str(intent.get("status") or "").strip()
            if device_id is None or not status:
                raise ValueError("DeepSeek 返回的设备控制指令缺少 device_id 或 status。")
            device = self.set_device_status(user, device_id, status)
            return {
                "type": "device",
                "message": reply or f"{device['name']} 已切换为 {device['status']}。",
                "device": device,
                "source": "deepseek",
            }

        if action == "activate_scene":
            scene_id = self._intent_int(intent, "scene_id")
            if scene_id is None:
                raise ValueError("DeepSeek 返回的场景指令缺少 scene_id。")
            scene = self.activate_scene(user, scene_id)
            return {
                "type": "scene",
                "message": reply or f"已启动{scene['name']}。",
                "scene": scene,
                "source": "deepseek",
            }

        if action == "simulate_alert":
            room_id = self._intent_int(intent, "room_id") or self._room_from_command(command) or 1
            event_type = str(intent.get("event_type") or "").strip()
            if event_type not in ALERT_EVENT_TYPES:
                raise ValueError("DeepSeek 返回的告警事件类型不支持。")
            alert = self.simulate_alert(user, event_type, room_id)
            return {
                "type": "alert",
                "message": reply or alert["message"],
                "alert": alert,
                "source": "deepseek",
            }

        if action == "query_camera":
            device_id = self._intent_int(intent, "device_id")
            if device_id is None:
                raise ValueError("DeepSeek 返回的摄像头查询指令缺少 device_id。")
            camera = self.device(device_id)
            if camera["type"] != "camera":
                raise ValueError("DeepSeek 返回的摄像头设备类型不正确。")
            self.log(user, "deepseek_query_camera", "device", camera["id"], command)
            return {
                "type": "camera",
                "message": reply or f"正在查看{camera['name']}。",
                "device": camera,
                "source": "deepseek",
            }

        raise ValueError(reply or "DeepSeek 未识别出可执行的智能家居指令。")

    @staticmethod
    def _intent_int(intent: dict[str, Any], key: str) -> int | None:
        value = intent.get(key)
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"DeepSeek 返回的 {key} 不是有效数字。") from exc

    def deepseek_config(self, user: dict[str, Any]) -> dict[str, Any]:
        self.auth.require(user, {"admin", "member", "guest"})
        return self.deepseek_store.summary()

    def save_deepseek_config(
        self,
        user: dict[str, Any],
        api_key: str,
        base_url: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        self.auth.require(user, {"admin", "member"})
        if not (api_key or "").strip():
            raise ValueError("DeepSeek API 密钥不能为空。")
        self.deepseek_store.save(api_key, base_url=base_url, model=model)
        self.log(user, "save_deepseek_config", "system", None, "保存 DeepSeek API 密钥。")
        return self.deepseek_config(user)

    def test_deepseek_connection(self, user: dict[str, Any]) -> dict[str, Any]:
        self.auth.require(user, {"admin", "member"})
        result = self.deepseek.test_connection()
        self.log(user, "test_deepseek_connection", "system", None, result["message"])
        return result

    def logs(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.db.query_all(
            """
            SELECT l.*, u.display_name AS user_name
            FROM operation_logs l
            LEFT JOIN users u ON u.id = l.user_id
            ORDER BY l.created_at DESC, l.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def log(
        self,
        user: dict[str, Any] | None,
        action: str,
        target_type: str,
        target_id: int | None,
        detail: str,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO operation_logs(user_id, action, target_type, target_id, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user["id"] if user else None, action, target_type, target_id, detail, utc_now()),
        )

    def _best_device_for_event(self, room_id: int, event_type: str) -> dict[str, Any] | None:
        if event_type == "smoke":
            return self.db.query_one("SELECT * FROM devices WHERE room_id = ? AND type = 'sensor'", (room_id,))
        if event_type in {"intrusion", "fall", "motion"}:
            return self._camera_for_room(room_id)
        if event_type == "door_open":
            return self.db.query_one("SELECT * FROM devices WHERE type = 'sensor' AND name LIKE '%门窗%'")
        return self.db.query_one("SELECT * FROM devices WHERE room_id = ? LIMIT 1", (room_id,))

    def _camera_for_room(self, room_id: int) -> dict[str, Any] | None:
        camera = self.db.query_one("SELECT * FROM devices WHERE room_id = ? AND type = 'camera'", (room_id,))
        if camera:
            return camera
        return self.db.query_one("SELECT * FROM devices WHERE type = 'camera' ORDER BY id LIMIT 1")

    def _apply_emergency_linkage(self, room_id: int, event_type: str) -> None:
        if event_type in {"intrusion", "smoke", "fall"}:
            now = utc_now()
            self.db.execute("UPDATE devices SET status = 'active', updated_at = ? WHERE type = 'alarm'", (now,))
            self.db.execute("UPDATE devices SET status = 'on', updated_at = ? WHERE room_id = ? AND type = 'light'", (now, room_id))
            if event_type == "intrusion":
                self.db.execute("UPDATE devices SET status = 'active', updated_at = ? WHERE type = 'camera'", (now,))

    def _scene_from_command(self, command: str) -> dict[str, Any] | None:
        for scene in self.scenes():
            if scene["name"] in command or scene["name"].replace("模式", "") in command:
                return scene
        aliases = {"离家": "离家安防", "回家": "回家模式", "夜间": "夜间巡航", "紧急": "紧急警戒"}
        for key, scene_name in aliases.items():
            if key in command:
                return self.db.query_one("SELECT * FROM scenes WHERE name = ?", (scene_name,))
        return None

    @staticmethod
    def _event_from_command(command: str) -> str | None:
        mapping = {
            "入侵": "intrusion",
            "陌生人": "intrusion",
            "烟雾": "smoke",
            "烟感": "smoke",
            "跌倒": "fall",
            "门窗": "door_open",
            "开门": "door_open",
            "移动": "motion",
        }
        if "模拟" not in command and "触发" not in command and "报警" not in command:
            return None
        for key, event_type in mapping.items():
            if key in command:
                return event_type
        return None

    def _room_from_command(self, command: str) -> int | None:
        for room in self.rooms():
            if room["name"] in command:
                return room["id"]
        return None

    def _device_from_command(self, command: str) -> dict[str, Any] | None:
        room_id = self._room_from_command(command)
        type_keywords = [
            ("灯", "light"),
            ("空调", "climate"),
            ("门锁", "lock"),
            ("锁", "lock"),
            ("警报", "alarm"),
            ("报警器", "alarm"),
            ("摄像头", "camera"),
        ]
        target_type = next((device_type for key, device_type in type_keywords if key in command), None)
        if not target_type:
            return None
        candidates = self.devices()
        if room_id:
            candidates = [device for device in candidates if device["room_id"] == room_id]
        for device in candidates:
            if device["type"] == target_type:
                return device
        return None

    def _camera_query_from_command(self, command: str) -> dict[str, Any] | None:
        if "查看" not in command and "看" not in command:
            return None
        room_id = self._room_from_command(command)
        cameras = [device for device in self.devices() if device["type"] == "camera"]
        if room_id:
            cameras = [device for device in cameras if device["room_id"] == room_id]
        return cameras[0] if cameras else None

    @staticmethod
    def _status_from_command(command: str, device_type: str) -> str:
        if device_type == "lock":
            if any(word in command for word in ["解锁", "开锁", "打开", "开启"]):
                return "unlocked"
            if any(word in command for word in ["上锁", "锁上", "关闭", "关上", "布防", "启动"]):
                return "locked"
            return "locked"
        if any(word in command for word in ["关闭", "关掉", "停止"]):
            if device_type == "camera":
                return "privacy"
            if device_type == "alarm":
                return "standby"
            if device_type == "sensor":
                return "normal"
            return "off" if device_type in {"light", "climate"} else "standby"
        if any(word in command for word in ["打开", "开启", "启动"]):
            if device_type == "climate":
                return "cooling"
            if device_type == "camera":
                return "active"
            if device_type == "alarm":
                return "active"
            return "on"
        if "布防" in command:
            return "armed"
        if "隐私" in command:
            return "privacy"
        return "on"


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("T", " "))
