# 软件设计文档

## 1. 文档目的

本文档描述“全屋智能安防与语音控制系统”的总体架构、模块划分、数据库设计、接口设计、界面设计和关键流程设计。本文档对应课程考核要求中的“2.2 软件设计”和评分标准中的“软件设计 20%”。

## 2. 设计目标

- 满足需求分析文档中的核心功能需求。
- 采用分层架构，避免界面、业务逻辑和数据访问混杂。
- 以可运行原型为中心，保证课堂演示稳定。
- 使用 SQLite 保存系统状态，保证重启后数据不丢失。
- 保持模块化和可测试性，方便扩展真实摄像头、真实语音识别和真实 IoT 网关。

## 3. 总体架构

系统采用四层架构：

| 层次 | 职责 | 对应实现 |
|---|---|---|
| 表现层 | 登录页、监控看板、设备控制、告警、录像、语音交互 | `src/web/index.html`、`styles.css`、`app.js` |
| 接口层 | 提供 HTTP JSON API，处理请求路由和错误响应 | `src/smart_home/server.py` |
| 业务逻辑层 | 认证、设备管理、告警联动、录像、语音解析、场景模式 | `src/smart_home/auth.py`、`services.py` |
| 数据访问层 | SQLite 连接、建表、种子数据、通用查询 | `src/smart_home/database.py` |

架构图原始素材：`diagrams/architecture.mmd`。

## 4. 模块设计

| 模块 | 主要职责 | 关键文件 |
|---|---|---|
| 认证与权限模块 | 登录、令牌管理、角色权限校验、密码哈希 | `auth.py` |
| 设备管理模块 | 设备列表、状态更新、房间归属、设备类型管理 | `services.py` |
| 监控与录像模块 | 摄像头列表、模拟视频展示、录像记录与检索 | `services.py`、`app.js` |
| 告警与联动模块 | 异常事件生成、告警状态、录像创建、设备联动 | `services.py` |
| 语音指令模块 | 通过 DeepSeek 或本地规则解析中文指令，路由到设备、告警、场景或摄像头查询 | `services.py`、`deepseek.py` |
| 场景模式模块 | 离家安防、回家模式、夜间巡航、紧急警戒 | `services.py` |
| 审计日志模块 | 记录关键操作，供管理员追溯 | `services.py` |
| 前端工作台 | 数据展示、按钮操作、表单提交、状态刷新 | `app.js` |

## 5. 数据库设计

数据库：`data/smart_home.sqlite`。

ER 图原始素材：`diagrams/er-diagram.mmd`。

### 5.1 用户表 users

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 用户编号 |
| username | TEXT UNIQUE | 登录用户名 |
| password_hash | TEXT | 密码哈希 |
| role | TEXT | admin / member / guest |
| display_name | TEXT | 展示名称 |
| created_at | TEXT | 创建时间 |

### 5.2 房间表 rooms

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 房间编号 |
| name | TEXT UNIQUE | 房间名称 |
| floor | TEXT | 楼层 |
| description | TEXT | 房间说明 |

### 5.3 设备表 devices

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 设备编号 |
| room_id | INTEGER FK | 所属房间 |
| name | TEXT | 设备名称 |
| type | TEXT | camera / sensor / light / climate / lock / alarm |
| status | TEXT | 设备状态 |
| battery | INTEGER | 电量 |
| online | INTEGER | 在线状态 |
| metadata_json | TEXT | 扩展信息 |
| updated_at | TEXT | 更新时间 |

### 5.4 告警表 alerts

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 告警编号 |
| room_id | INTEGER FK | 告警房间 |
| device_id | INTEGER FK | 触发设备 |
| event_type | TEXT | intrusion / smoke / fall / door_open / motion |
| severity | TEXT | low / medium / high / critical |
| status | TEXT | open / acknowledged / resolved |
| message | TEXT | 告警信息 |
| triggered_at | TEXT | 触发时间 |
| resolved_at | TEXT | 处理时间 |
| resolution_note | TEXT | 处置说明 |

### 5.5 录像表 recordings

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 录像编号 |
| room_id | INTEGER FK | 房间 |
| camera_device_id | INTEGER FK | 摄像头 |
| title | TEXT | 录像标题 |
| event_type | TEXT | 事件类型 |
| started_at | TEXT | 开始时间 |
| duration_seconds | INTEGER | 时长 |
| storage_path | TEXT | 模拟存储路径 |
| summary | TEXT | 录像摘要 |

### 5.6 场景与日志表

- `scenes`：场景名称、说明和当前激活状态。
- `scene_actions`：场景与设备目标状态的映射。
- `automation_rules`：异常事件和联动策略配置，业务层会读取 enabled 状态决定是否执行设备联动。
- `operation_logs`：用户操作审计日志。

## 6. 接口设计

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| GET | `/health` | 健康检查 | 无 |
| POST | `/api/login` | 用户登录 | 无 |
| GET | `/api/session` | 获取当前用户 | 登录用户 |
| GET | `/api/dashboard` | 获取看板数据 | 登录用户 |
| GET | `/api/devices` | 获取设备列表 | 登录用户 |
| PATCH | `/api/devices/{id}` | 更新设备状态 | admin/member |
| GET | `/api/alerts` | 获取告警列表 | 登录用户 |
| POST | `/api/alerts/simulate` | 触发模拟告警 | admin/member |
| POST | `/api/alerts/{id}/resolve` | 处理告警 | admin/member |
| GET | `/api/recordings` | 检索录像 | 登录用户 |
| POST | `/api/voice` | 执行语音指令 | admin/member |
| GET | `/api/deepseek/config` | 获取 DeepSeek 配置摘要 | 登录用户 |
| POST | `/api/deepseek/config` | 保存 DeepSeek API 密钥 | admin/member |
| POST | `/api/deepseek/test` | 测试 DeepSeek 连接 | admin/member |
| GET | `/api/scenes` | 获取场景列表 | 登录用户 |
| POST | `/api/scenes/{id}/activate` | 启动场景 | admin/member |
| GET | `/api/logs` | 获取审计日志 | admin |

## 7. 关键流程设计

### 7.1 异常告警与联动

1. 前端提交事件类型和房间。
2. 接口层校验登录令牌。
3. 业务层创建告警记录。
4. 业务层创建录像记录。
5. 业务层读取 `automation_rules`，仅在对应规则启用时执行联动策略。
6. 写入审计日志。
7. 前端刷新看板，展示告警和设备变化。
8. 用户确认处理告警后，业务层将告警状态更新为 resolved；若已无其他未处理告警，则将声光警报器恢复为 standby。

顺序图原始素材：`diagrams/sequence-alert.puml`。

### 7.2 语音指令解析

系统按优先级解析语音指令：

1. 若已保存 DeepSeek API 密钥，优先把用户中文指令转换为受控 JSON 动作。
2. DeepSeek 返回结果需经过设备、场景、事件类型和状态校验，避免编造不存在的资源。
3. DeepSeek 未配置或解析失败时，回退到本地规则解析。
4. 本地规则依次判断场景模式、告警模拟、摄像头查询和设备控制。
5. 无法识别时返回提示。

活动图原始素材：`diagrams/activity-voice.mmd`。

## 8. 界面设计

系统为单页 Web 工作台：

- 登录区：账号、密码、演示账号提示。
- 监控总览：房间数、设备数、在线数、摄像头数、未处理告警数。
- 实时监控：多摄像头模拟视频卡片。
- 语音与场景：DeepSeek 配置、语音指令输入框和场景模式卡片。
- 告警中心：模拟告警触发、告警列表、确认处理。
- 录像回放：关键词检索和录像摘要展示。
- 设备控制：按设备卡片控制状态。
- 审计日志：管理员查看关键操作。

界面风格以操作台为核心，避免营销页式设计，优先保证信息密度、可扫描性和演示效率。

## 9. 可扩展性设计

- 可将 `services.py` 中的规则检测替换为真实计算机视觉服务。
- 可将 SQLite 替换为 MySQL/PostgreSQL。
- 可将文本语音指令替换为浏览器语音识别或离线 ASR。
- 可将模拟设备状态接入 MQTT、Home Assistant 或厂商 IoT 网关。
- 可将本地令牌机制替换为 JWT 或服务端会话。

## 10. 设计图表

- `diagrams/architecture.mmd`：总体架构图。
- `diagrams/er-diagram.mmd`：ER 图。
- `diagrams/sequence-alert.puml`：告警联动顺序图。
- `diagrams/activity-voice.mmd`：语音指令活动图。
- `diagrams/state-alert.mmd`：告警状态图。
