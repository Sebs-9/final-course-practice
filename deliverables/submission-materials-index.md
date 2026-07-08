# 提交材料索引

## 1. 文档材料

| 要求 | 对应文件 |
|---|---|
| 需求分析文档 | `docs/requirements.md` |
| 软件设计文档 | `docs/design.md` |
| 测试计划与用例报告 | `docs/test-plan-and-cases.md` |
| 项目管理文档 | `docs/project-management.md` |
| 部署与操作说明 | `docs/deployment-and-user-guide.md` |
| 成员分工与课程实践心得 | `docs/team-work-and-reflection-template.md` |
| 版本管理记录 | `docs/version-history.md` |

## 2. 图表原始素材

| 图表 | 对应文件 |
|---|---|
| 用例图 | `diagrams/use-case.puml` |
| 总体架构图 | `diagrams/architecture.mmd` |
| ER 图 | `diagrams/er-diagram.mmd` |
| 告警联动顺序图 | `diagrams/sequence-alert.puml` |
| 语音指令活动图 | `diagrams/activity-voice.mmd` |
| 告警状态图 | `diagrams/state-alert.mmd` |
| 项目甘特图 | `diagrams/gantt.mmd` |

## 3. 程序代码和测试数据

| 内容 | 对应路径 |
|---|---|
| 系统启动入口 | `src/run.py` |
| 后端认证、数据库、业务服务、HTTP 接口 | `src/smart_home/` |
| 前端页面、样式和交互脚本 | `src/web/` |
| 自动化测试 | `tests/test_services.py`、`tests/test_http_api.py` |
| 测试数据 | `src/smart_home/database.py` 中的种子数据；运行后自动生成 `data/smart_home.sqlite` |

## 4. 演示和视频材料

| 要求 | 对应文件或处理方式 |
|---|---|
| 5 分钟课堂演示材料 | 已由小组完成；项目内保留 `docs/presentation-outline.md` 作为提纲 |
| 15 分钟项目汇报视频 | 按 `docs/report-video-script.md` 录制 |
| 界面截图 | `assets/dashboard-authenticated.png`，可补充当前版本截图 |
| 实际录屏视频 | 录制完成后放入最终提交包 |

## 5. 当前验证结果

| 检查项 | 结果 |
|---|---|
| 自动化测试 | `python -m unittest discover -s tests -v`，31 个测试通过 |
| 本地启动 | `python src/run.py` 后访问 `http://127.0.0.1:8000` |
| 演示账号 | `admin/Admin@SE2026!`、`member/Member@SE2026!`、`guest/Guest@SE2026!` |
| DeepSeek 功能 | 使用本机代理 `127.0.0.1:7897` 测试通过；密钥采用本地配置和脱敏展示 |

## 6. 对图片中提交要求的对应

| 图片编号 | 要求 | 当前状态 |
|---|---|---|
| 1 | 需求、设计、测试、项目管理文档及 UML、甘特图素材 | 已整理 |
| 2 | 程序代码、测试数据、执行视频或界面截图、部署说明 | 代码、测试、部署说明和截图已整理 |
| 3 | 组长提供成员分工说明，成员提供 400 字以内心得 | 已按 6 名组员整理 |
| 4 | 5 分钟演示材料 | 已完成，项目内保留演示提纲 |
| 5 | 15 分钟项目汇报视频 | 已提供项目汇报视频脚本 |
