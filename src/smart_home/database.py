from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable


def utc_now() -> str:
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


class Database:
    def __init__(self, path: str | Path):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.conn.close()

    def execute(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Cursor:
        with self.conn:
            return self.conn.execute(sql, tuple(params))

    def executemany(self, sql: str, rows: Iterable[Iterable[Any]]) -> None:
        with self.conn:
            self.conn.executemany(sql, rows)

    def query_one(self, sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        row = self.conn.execute(sql, tuple(params)).fetchone()
        return dict(row) if row else None

    def query_all(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        rows = self.conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def init_schema(self) -> None:
        schema = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'member', 'guest')),
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                floor TEXT NOT NULL,
                description TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL REFERENCES rooms(id),
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                battery INTEGER NOT NULL DEFAULT 100,
                online INTEGER NOT NULL DEFAULT 1,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL REFERENCES rooms(id),
                device_id INTEGER REFERENCES devices(id),
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL CHECK(severity IN ('low', 'medium', 'high', 'critical')),
                status TEXT NOT NULL CHECK(status IN ('open', 'acknowledged', 'resolved')),
                message TEXT NOT NULL,
                triggered_at TEXT NOT NULL,
                resolved_at TEXT,
                resolution_note TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL REFERENCES rooms(id),
                camera_device_id INTEGER NOT NULL REFERENCES devices(id),
                title TEXT NOT NULL,
                event_type TEXT NOT NULL,
                started_at TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                storage_path TEXT NOT NULL,
                summary TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS scene_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scene_id INTEGER NOT NULL REFERENCES scenes(id),
                device_id INTEGER NOT NULL REFERENCES devices(id),
                target_status TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                action_summary TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                action TEXT NOT NULL,
                target_type TEXT NOT NULL,
                target_id INTEGER,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
        ]
        for statement in schema:
            self.execute(statement)

    def seed(self) -> None:
        existing = self.query_one("SELECT COUNT(*) AS count FROM rooms")
        if existing and existing["count"] > 0:
            return

        from .auth import hash_password

        now = utc_now()
        self.executemany(
            """
            INSERT INTO users(username, password_hash, role, display_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("admin", hash_password("admin123"), "admin", "系统管理员", now),
                ("member", hash_password("member123"), "member", "家庭成员", now),
                ("guest", hash_password("guest123"), "guest", "访客查看者", now),
            ],
        )

        rooms = [
            ("玄关", "1F", "入户门、门锁和门口摄像头区域"),
            ("客厅", "1F", "家庭主要活动区域，包含灯光、摄像头和空调"),
            ("卧室", "2F", "休息区域，包含摄像头和空调"),
            ("厨房", "1F", "烟雾、燃气与用电风险重点区域"),
            ("阳台", "1F", "门窗传感器和外围防护区域"),
        ]
        self.executemany("INSERT INTO rooms(name, floor, description) VALUES (?, ?, ?)", rooms)

        devices = [
            (1, "门口摄像头", "camera", "active", 100, 1, {"stream": "foyer", "angle": "wide"}),
            (2, "客厅摄像头", "camera", "active", 100, 1, {"stream": "living", "angle": "panorama"}),
            (3, "卧室摄像头", "camera", "privacy", 100, 1, {"stream": "bedroom", "angle": "fixed"}),
            (1, "智能门锁", "lock", "locked", 82, 1, {"lockMode": "auto"}),
            (5, "阳台门窗传感器", "sensor", "armed", 76, 1, {"contact": "closed"}),
            (4, "厨房烟雾传感器", "sensor", "normal", 91, 1, {"threshold": "medium"}),
            (2, "客厅灯光", "light", "off", 100, 1, {"brightness": 0}),
            (3, "卧室空调", "climate", "off", 100, 1, {"temperature": 26}),
            (2, "声光警报器", "alarm", "standby", 100, 1, {"volume": "high"}),
        ]
        self.executemany(
            """
            INSERT INTO devices(room_id, name, type, status, battery, online, metadata_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (room_id, name, device_type, status, battery, online, json.dumps(meta, ensure_ascii=False), now)
                for room_id, name, device_type, status, battery, online, meta in devices
            ],
        )

        scenes = [
            ("离家安防", "关闭灯光，门锁上锁，传感器布防，摄像头开启。", 0),
            ("回家模式", "关闭警报器，打开客厅灯，恢复舒适环境。", 0),
            ("夜间巡航", "客厅灯关闭，门窗布防，摄像头保持巡航。", 0),
            ("紧急警戒", "开启声光警报器，打开客厅灯，所有摄像头激活。", 0),
        ]
        self.executemany("INSERT INTO scenes(name, description, is_active) VALUES (?, ?, ?)", scenes)

        scene_actions = [
            (1, 4, "locked"), (1, 5, "armed"), (1, 7, "off"), (1, 1, "active"), (1, 2, "active"),
            (2, 9, "standby"), (2, 7, "on"), (2, 8, "cooling"),
            (3, 5, "armed"), (3, 7, "off"), (3, 1, "active"), (3, 2, "active"),
            (4, 9, "active"), (4, 7, "on"), (4, 1, "active"), (4, 2, "active"), (4, 3, "active"),
        ]
        self.executemany(
            "INSERT INTO scene_actions(scene_id, device_id, target_status) VALUES (?, ?, ?)",
            scene_actions,
        )

        rules = [
            ("入侵联动", "intrusion", "触发高危告警，打开客厅灯，启动声光警报器。", 1),
            ("烟雾联动", "smoke", "触发紧急告警，启动声光警报器并记录厨房录像。", 1),
            ("跌倒联动", "fall", "触发紧急告警，记录事件并提示联系家属。", 1),
            ("门窗异常", "door_open", "触发中危告警，保留门窗传感器事件。", 1),
        ]
        self.executemany(
            "INSERT INTO automation_rules(name, trigger_type, action_summary, enabled) VALUES (?, ?, ?, ?)",
            rules,
        )

        base = datetime.now().replace(microsecond=0)
        recordings = [
            (1, 1, "门口夜间巡查片段", "routine", base - timedelta(hours=8), 42, "/recordings/foyer-night.mp4", "门口无异常通行。"),
            (2, 2, "客厅活动检测片段", "motion", base - timedelta(hours=5), 55, "/recordings/living-motion.mp4", "检测到家庭成员活动。"),
            (4, 1, "厨房烟雾传感器自检", "smoke-test", base - timedelta(days=1), 30, "/recordings/kitchen-test.mp4", "烟雾传感器完成自检。"),
            (5, 1, "阳台门窗巡查片段", "routine", base - timedelta(days=1, hours=3), 38, "/recordings/balcony-check.mp4", "门窗保持关闭。"),
        ]
        self.executemany(
            """
            INSERT INTO recordings(room_id, camera_device_id, title, event_type, started_at, duration_seconds, storage_path, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (room_id, camera_id, title, event_type, started_at.isoformat(sep=" "), duration, path, summary)
                for room_id, camera_id, title, event_type, started_at, duration, path, summary in recordings
            ],
        )

        self.execute(
            """
            INSERT INTO operation_logs(user_id, action, target_type, target_id, detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (1, "seed", "system", None, "初始化演示数据。", now),
        )
