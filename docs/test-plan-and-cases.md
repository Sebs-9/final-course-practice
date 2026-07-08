# 测试计划与用例报告

## 1. 文档目的

本文档定义“全屋智能安防与语音控制系统”的测试目标、范围、方法、环境、测试用例和测试结果。本文档对应课程考核要求中的“2.3 系统测试”和评分标准中的“系统测试 15%”。

## 2. 测试目标

- 验证系统核心功能是否符合需求分析文档。
- 验证权限控制、设备控制、告警联动、录像检索、语音指令和场景模式是否正确。
- 验证系统能在本地环境中稳定启动和运行。
- 为最终提交提供可复现的测试结果。

## 3. 测试范围

范围内：

- 登录与权限。
- 设备状态控制。
- 异常告警生成与处置。
- 告警联动策略。
- 录像记录检索。
- 语音指令解析。
- 场景模式切换。
- 审计日志。

范围外：

- 真实摄像头视频质量测试。
- 真实语音识别准确率测试。
- 真实短信、电话、移动端推送测试。
- 公网压力测试。

## 4. 测试环境

| 项目 | 内容 |
|---|---|
| 操作系统 | Windows |
| Python | Python 3.10 或更高版本 |
| 数据库 | SQLite |
| 浏览器 | Chrome / Edge |
| 测试框架 | Python `unittest` |
| 测试日期 | 2026-07-08 |

## 5. 自动化测试执行

执行命令：

```powershell
python -m unittest discover -s tests -v
```

实际结果：

```text
Ran 29 tests in 6.909s

OK
```

## 6. 功能测试用例

| 编号 | 测试项 | 前置条件 | 操作步骤 | 期望结果 | 自动化覆盖 |
|---|---|---|---|---|---|
| TC-F01 | 正确登录 | 系统已初始化 | 输入 admin/Admin@SE2026! 登录 | 登录成功，进入工作台 | `test_login_success_returns_token_and_admin_user` |
| TC-F02 | 错误密码 | 系统已初始化 | 输入 admin/wrong 登录 | 系统拒绝登录 | `test_login_rejects_wrong_password` |
| TC-F03 | 访客越权控制 | guest 已登录 | 调用设备控制服务 | 抛出权限错误 | `test_guest_cannot_control_device` |
| TC-F04 | 控制客厅灯 | member 已登录 | 执行“打开客厅灯” | 客厅灯状态变为 on | `test_voice_command_turns_on_living_room_light` |
| TC-F05 | 查看摄像头 | member 已登录 | 执行“查看客厅摄像头” | 返回摄像头信息，不改变状态 | `test_voice_command_queries_camera_without_changing_status` |
| TC-F06 | 模拟入侵告警 | admin 已登录 | 触发玄关入侵 | 生成 open 告警，警报器启动，生成录像 | `test_simulate_alert_creates_recording_and_linkage` |
| TC-F07 | 录像检索 | 系统存在录像 | 搜索“厨房” | 返回厨房相关录像 | `test_recording_filter_by_keyword` |
| TC-F08 | 启动离家安防 | member 已登录 | 启动场景 1 | 门锁 locked，灯光 off | `test_scene_activation_updates_devices` |
| TC-F09 | 处理烟雾告警 | member 已登录 | 触发烟雾并处理 | 告警状态变为 resolved，警报器恢复 standby | `test_resolve_alert_updates_status` |
| TC-F10 | 多告警处理 | member 已登录 | 触发两个告警，仅处理其中一个 | 仍有未处理告警时警报器保持 active，全部处理后恢复 standby | `test_resolve_alert_keeps_alarm_active_when_other_alerts_are_open` |
| TC-F11 | DeepSeek 配置保存 | admin 已登录 | 保存 DeepSeek API 密钥 | 返回配置摘要，不泄露完整密钥 | `test_deepseek_config_save_masks_secret` |
| TC-F12 | DeepSeek 连接测试 | member 已登录且已保存密钥 | 调用测试连接接口 | 返回连接成功和模型信息 | `test_deepseek_test_connection_uses_saved_key` |
| TC-F13 | DeepSeek 语音解析 | member 已登录且已保存密钥 | 执行“帮我把客厅亮一点” | DeepSeek 解析为设备控制，客厅灯变为 on | `test_deepseek_voice_command_controls_device` |
| TC-F14 | DeepSeek 失败回退 | member 已登录且 DeepSeek 返回无效状态 | 执行本地规则可识别指令 | 系统回退本地规则并完成操作 | `test_deepseek_voice_falls_back_to_local_rules` |

## 7. 安全性测试用例

| 编号 | 测试项 | 操作 | 期望结果 |
|---|---|---|---|
| TC-S01 | 未登录访问看板 | 不带 Authorization 请求 `/api/dashboard` | 返回 401 |
| TC-S02 | 错误密码 | 使用错误密码登录 | 返回错误提示 |
| TC-S03 | 访客控制设备 | guest 调用设备控制接口 | 返回 403 |
| TC-S04 | 访客触发告警 | guest 调用模拟告警接口 | 返回 403 |
| TC-S05 | 非管理员查看日志 | member 调用 `/api/logs` | 返回 403 |
| TC-S06 | 访客保存 DeepSeek 密钥 | guest 调用 `/api/deepseek/config` | 返回 403 |
| TC-S07 | SQL 注入式用户名 | 使用特殊用户名登录 | 登录失败且服务正常 |
| TC-S08 | XSS 式录像关键词 | 搜索 `<script>alert(1)</script>` | 接口正常返回，前端转义展示 |

## 8. 兼容性测试用例

| 编号 | 环境 | 测试内容 | 期望结果 |
|---|---|---|---|
| TC-C01 | Windows + Chrome | 登录、看板、设备控制、语音指令 | 页面正常显示，功能可用 |
| TC-C02 | Windows + Edge | 登录、告警、录像检索 | 页面正常显示，功能可用 |
| TC-C03 | 窄屏浏览器窗口 | 页面布局缩放 | 卡片换行，无明显遮挡 |

## 9. 性能测试说明

由于本项目为本地课程原型，性能测试采用轻量方式：

- 登录、看板加载、设备控制、告警模拟等操作在本地环境中均应在 2 秒内返回。
- SQLite 数据量较小，查询响应可满足课程演示。
- 若后续接入真实视频流，应进一步测试视频延迟、并发访问和存储吞吐。

## 10. 缺陷记录

| 编号 | 缺陷描述 | 严重性 | 状态 |
|---|---|---|---|
| BUG-01 | “查看客厅摄像头”原先可能被误判为设备控制 | 中 | 已修复 |
| BUG-02 | 告警确认处理后，客厅声光警报器可能仍保持 active | 中 | 已修复 |

## 11. 测试结论

自动化测试覆盖了登录权限、设备控制、语音指令、DeepSeek 配置与回退、异常告警、录像检索、场景模式、告警处置和接口安全等关键路径。当前 29 个自动化测试全部通过，系统满足课程原型演示和测试报告要求。服务启动后，`/health` 返回 `{"status":"ok"}`，登录和看板接口可正常返回用户、设备、房间和摄像头统计。
