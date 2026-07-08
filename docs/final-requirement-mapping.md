# 课程要求对照说明

这份文件用于最终检查提交材料是否覆盖课程图片中列出的要求。详细内容分别写在需求、设计、测试和项目管理文档里，本文件只做索引和确认。

## 1. 文档类材料

| 要求 | 已准备文件 | 说明 |
|---|---|---|
| 需求分析文档 | `docs/requirements.md` | 包含项目背景、利益相关方、功能需求、非功能需求、核心用例和需求追踪矩阵。 |
| 软件设计文档 | `docs/design.md` | 包含分层架构、模块设计、数据库设计、接口设计、关键流程和界面设计。 |
| 测试计划与用例报告 | `docs/test-plan-and-cases.md` | 包含测试目标、测试环境、功能/安全/兼容性用例、缺陷记录和 31 个自动化测试结果。 |
| 项目管理文档 | `docs/project-management.md` | 包含 2 个月计划、6 人分工、任务拆分、风险管理和版本管理规范。 |
| 成员分工与心得 | `docs/team-work-and-reflection-template.md` | 按提供的真实分工列出丁天、张星宇、王胜航、包可豪、卢鹏宇、李智星 6 名成员的工作说明和 400 字以内心得。 |

## 2. 图表原始素材

图表统一放在 `diagrams/`：

| 图表 | 文件 |
|---|---|
| 用例图 | `diagrams/use-case.puml` |
| 架构图 | `diagrams/architecture.mmd` |
| ER 图 | `diagrams/er-diagram.mmd` |
| 告警联动顺序图 | `diagrams/sequence-alert.puml` |
| 语音指令活动图 | `diagrams/activity-voice.mmd` |
| 告警状态图 | `diagrams/state-alert.mmd` |
| 甘特图 | `diagrams/gantt.mmd` |

## 3. 程序、数据和运行材料

| 要求 | 已准备内容 |
|---|---|
| 程序代码 | `src/run.py`、`src/smart_home/`、`src/web/` |
| 测试代码 | `tests/test_services.py`、`tests/test_http_api.py` |
| 测试数据 | `src/smart_home/database.py` 中的种子数据，运行后生成 `data/smart_home.sqlite` |
| 部署和操作说明 | `docs/deployment-and-user-guide.md` |
| 界面截图 | `assets/dashboard-authenticated.png`、`assets/dashboard-current.png` |

系统已实现登录、权限、设备控制、监控看板、告警联动、录像回放、场景模式、语音指令、DeepSeek 解析、自动化规则和审计日志等功能。核心源码数量和代码规模满足课程项目要求。

## 4. 演示和视频材料

| 要求 | 当前状态 |
|---|---|
| 5 分钟课堂演示材料 | 小组已完成；项目内保留 `docs/presentation-outline.md` 作为提纲。 |
| 15 分钟汇报视频 | 已准备 `docs/report-video-script.md`，实际视频需录制后加入最终提交包。 |

## 5. 版本管理和质量验证

| 项目 | 当前状态 |
|---|---|
| Git 版本记录 | `docs/version-history.md` 记录真实提交历史。 |
| 自动化测试 | `python -m unittest discover -s tests -v`，31 个测试通过。 |
| DeepSeek 功能 | 已用本机代理 `127.0.0.1:7897` 做真实连接测试，提交包不包含 API key。 |
| 敏感文件 | `deepseekapi` 和 DeepSeek 配置文件不进入提交包。 |

## 6. 最终还需人工补充

如果按当前文件夹提交，材料已经覆盖文档、代码、图表、测试和截图。最后仍需人工补充的是实际视频文件：录制 15 分钟项目汇报视频后，放入最终提交包。
