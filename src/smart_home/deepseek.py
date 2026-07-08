from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"

HttpPost = Callable[[str, dict[str, str], dict[str, Any], float], dict[str, Any]]


@dataclass
class DeepSeekConfig:
    api_key: str = ""
    base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    model: str = DEFAULT_DEEPSEEK_MODEL

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key.strip())


class DeepSeekConfigStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> DeepSeekConfig:
        if not self.path.exists():
            return DeepSeekConfig()
        data = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        return DeepSeekConfig(
            api_key=str(data.get("api_key") or "").strip(),
            base_url=normalize_base_url(str(data.get("base_url") or DEFAULT_DEEPSEEK_BASE_URL)),
            model=str(data.get("model") or DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL,
        )

    def save(self, api_key: str, base_url: str | None = None, model: str | None = None) -> DeepSeekConfig:
        config = DeepSeekConfig(
            api_key=api_key.strip(),
            base_url=normalize_base_url(base_url or DEFAULT_DEEPSEEK_BASE_URL),
            model=(model or DEFAULT_DEEPSEEK_MODEL).strip() or DEFAULT_DEEPSEEK_MODEL,
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"api_key": config.api_key, "base_url": config.base_url, "model": config.model},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return config

    def summary(self) -> dict[str, Any]:
        config = self.load()
        return {
            "hasApiKey": config.has_api_key,
            "maskedApiKey": mask_api_key(config.api_key),
            "baseUrl": config.base_url,
            "model": config.model,
        }


class DeepSeekClient:
    def __init__(self, store: DeepSeekConfigStore, http_post: HttpPost | None = None):
        self.store = store
        self.http_post = http_post or default_http_post

    def test_connection(self) -> dict[str, Any]:
        config = self._require_config()
        response = self._chat(
            config,
            messages=[
                {"role": "system", "content": '请只输出 json：{"ok": true, "message": "connected"}'},
                {"role": "user", "content": "连接测试"},
            ],
            max_tokens=80,
        )
        content = extract_message_content(response)
        if not content:
            raise ValueError("DeepSeek 没有返回内容。")
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("DeepSeek 测试返回不是有效 JSON。") from exc
        if parsed.get("ok") is not True:
            raise ValueError("DeepSeek 测试返回未确认连接成功。")
        return {"ok": True, "message": f"DeepSeek 连接成功，模型 {config.model} 可用。", "model": config.model}

    def parse_voice_command(
        self,
        command: str,
        rooms: list[dict[str, Any]],
        devices: list[dict[str, Any]],
        scenes: list[dict[str, Any]],
        status_options: dict[str, set[str]],
        event_types: set[str],
    ) -> dict[str, Any]:
        config = self._require_config()
        room_payload = [{"id": room["id"], "name": room["name"]} for room in rooms]
        device_payload = [
            {
                "id": device["id"],
                "name": device["name"],
                "room_id": device["room_id"],
                "room_name": device["room_name"],
                "type": device["type"],
                "status": device["status"],
                "allowed_status": sorted(status_options.get(device["type"], set())),
            }
            for device in devices
        ]
        scene_payload = [
            {"id": scene["id"], "name": scene["name"], "description": scene["description"]}
            for scene in scenes
        ]
        schema_example = {
            "action": "set_device",
            "device_id": 7,
            "status": "on",
            "scene_id": None,
            "room_id": None,
            "event_type": None,
            "reply": "已打开客厅灯。",
        }
        system_prompt = f"""
你是智能家居语音指令解析器，只能输出 json，不能输出 Markdown。
你的任务是把用户中文指令转换为一个受控动作。不要编造设备、房间、场景或状态。

允许 action：
- set_device：控制某个设备，必须给 device_id 和 status。
- activate_scene：启动场景，必须给 scene_id。
- simulate_alert：模拟告警，必须给 room_id 和 event_type。
- query_camera：查看摄像头，必须给 device_id，且设备类型必须是 camera。
- none：无法识别或只是闲聊。

允许告警 event_type：{sorted(event_types)}
输出 JSON 示例：{json.dumps(schema_example, ensure_ascii=False)}
房间：{json.dumps(room_payload, ensure_ascii=False)}
设备：{json.dumps(device_payload, ensure_ascii=False)}
场景：{json.dumps(scene_payload, ensure_ascii=False)}
""".strip()
        response = self._chat(
            config,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": command}],
            max_tokens=360,
        )
        content = extract_message_content(response)
        if not content:
            raise ValueError("DeepSeek 没有返回可解析的指令。")
        try:
            intent = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("DeepSeek 返回的指令不是有效 JSON。") from exc
        if not isinstance(intent, dict):
            raise ValueError("DeepSeek 返回的指令格式不正确。")
        return intent

    def _require_config(self) -> DeepSeekConfig:
        config = self.store.load()
        if not config.has_api_key:
            raise ValueError("请先保存 DeepSeek API 密钥。")
        return config

    def _chat(self, config: DeepSeekConfig, messages: list[dict[str, str]], max_tokens: int) -> dict[str, Any]:
        payload = {
            "model": config.model,
            "messages": messages,
            "stream": False,
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        return self.http_post(
            f"{config.base_url}/chat/completions",
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.api_key}",
            },
            payload,
            12.0,
        )


def normalize_base_url(value: str) -> str:
    base_url = (value or DEFAULT_DEEPSEEK_BASE_URL).strip().rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("DeepSeek API 地址必须以 http:// 或 https:// 开头。")
    return base_url


def mask_api_key(api_key: str) -> str:
    api_key = api_key.strip()
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return f"{api_key[:2]}***{api_key[-2:]}"
    return f"{api_key[:4]}...{api_key[-4:]}"


def extract_message_content(response: dict[str, Any]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        return ""
    return str(message.get("content") or "").strip()


def default_http_post(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw or "{}")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(f"DeepSeek 连接失败（HTTP {exc.code}）：{extract_error_message(detail)}") from exc
    except URLError as exc:
        raise ValueError(f"DeepSeek 连接失败：{exc.reason}") from exc
    except TimeoutError as exc:
        raise ValueError("DeepSeek 连接超时。") from exc


def extract_error_message(detail: str) -> str:
    try:
        payload = json.loads(detail or "{}")
    except json.JSONDecodeError:
        return detail[:160] or "未知错误"
    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("type") or "未知错误")
    return str(payload.get("message") or detail[:160] or "未知错误")
