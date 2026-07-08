# 与课程考核 PDF 要求的对应关系

## 1. 选题要求

PDF 要求：从三个选题方向中任选一项，完成软件开发项目相关的一系列活动。

本项目对应：

- 选择“选题方向一：全屋智能系统”。
- 具体项目为“全屋智能安防与语音控制系统”。
- 功能覆盖选题说明中的“家居视频监控与安防智能系统设计”，并加入“智能家居语音交互助手系统”的核心语音控制能力。

## 2. 2.1 需求分析

PDF 要求：

- 描述功能性与非功能性需求。
- 绘制必要 UML 图，如用例图、类图、状态图等。
- 提交需求分析文档。

本项目对应：

- `docs/requirements.md`
- `diagrams/use-case.puml`
- `diagrams/state-alert.mmd`
- `diagrams/activity-voice.mmd`

覆盖内容：

- 功能需求：登录、设备控制、实时监控、异常告警、录像回放、语音指令、场景模式、审计日志。
- 非功能需求：性能、可靠性、安全性、兼容性、可维护性、可测试性。
- 核心用例：登录、查看监控、控制设备、告警处理、录像检索、语音指令、管理审计。

## 3. 2.2 软件设计

PDF 要求：

- 涵盖总体架构、模块详细设计、数据库设计、接口设计、界面设计。
- 绘制构件图、活动图、顺序图等。
- 提交软件设计文档。

本项目对应：

- `docs/design.md`
- `diagrams/architecture.mmd`
- `diagrams/er-diagram.mmd`
- `diagrams/sequence-alert.puml`
- `diagrams/activity-voice.mmd`

覆盖内容：

- 总体架构：表现层、接口层、业务逻辑层、数据访问层和数据存储层。
- 模块设计：认证、设备、监控、告警、录像、语音、场景、日志。
- 数据库设计：users、rooms、devices、alerts、recordings、scenes、scene_actions、operation_logs。
- 接口设计：登录、看板、设备、告警、录像、语音、场景和日志 API。
- 界面设计：登录页、监控工作台、告警中心、录像回放、设备控制、审计日志。

## 4. 2.3 系统测试

PDF 要求：

- 展示测试规划、测试用例设计、测试结果和结论。
- 包括功能、性能、安全、兼容性测试。
- 提交测试计划与用例报告。

本项目对应：

- `docs/test-plan-and-cases.md`
- `tests/test_services.py`

覆盖内容：

- 功能测试：登录、设备控制、告警、录像、语音、场景。
- 安全测试：错误密码、未登录、访客越权、日志权限。
- 兼容性测试：Windows + Chrome / Edge。
- 自动化测试结果：29 个测试全部通过。

## 5. 2.4 项目管理

PDF 要求：

- 假设项目执行期为 2 个月。
- 包含项目计划、团队成员分工、进度跟踪、风险管理。
- 体现项目管理规范性和有效性。
- 提交项目管理文档。

本项目对应：

- `docs/project-management.md`
- `diagrams/gantt.mmd`
- `docs/team-work-and-reflection-template.md`

覆盖内容：

- 2 个月里程碑计划。
- 6 名组员真实角色分工与课程实践心得。
- 任务拆分和状态记录。
- 风险识别、概率影响和应对策略。
- 版本管理规范和质量保障措施。

## 6. 2.5 系统原型与实现代码

PDF 要求：

- 提交代码和数据文件。
- 代码完整、可启动、功能正确。
- 具备可扩展性和可维护性。
- 对应文档中的关键模型和信息。
- 避免规模过小：实现用例不少于 3 个，源文件不少于 5 个，关键代码行数不少于 500 行。

本项目对应：

- `src/run.py`
- `src/smart_home/database.py`
- `src/smart_home/auth.py`
- `src/smart_home/services.py`
- `src/smart_home/server.py`
- `src/web/index.html`
- `src/web/styles.css`
- `src/web/app.js`
- `data/smart_home.sqlite`，启动后自动生成。
- `tests/test_services.py`

覆盖内容：

- 可运行 Web 原型。
- 自动建表和种子数据。
- 登录、权限、设备、告警、录像、语音、场景和日志完整闭环。
- 源文件数量超过 5 个。
- 实现用例超过 3 个。
- 关键代码行数超过 500 行。

## 7. 三、提交材料

PDF 要求：

- 提交需求分析、软件设计、测试计划与用例报告、项目管理文档。
- 提交 UML 图、甘特图等插图原始素材。
- 提交程序代码、测试数据、执行视频或界面截图、部署和操作说明。
- 组长提供成员分工说明，成员提供 400 字以内心得。
- 准备 5 分钟演示材料和 15 分钟汇报视频。

本项目对应：

- 文档：`docs/`
- 图表原始素材：`diagrams/`
- 程序代码：`src/`
- 测试代码：`tests/`
- 测试数据和数据库：`data/`
- 部署说明：`docs/deployment-and-user-guide.md`
- 成员分工与心得：`docs/team-work-and-reflection-template.md`
- 演示提纲：`docs/presentation-outline.md`
- 15 分钟汇报视频脚本：`docs/report-video-script.md`
- 提交检查清单：`deliverables/submission-checklist.md`

## 8. 四、评分标准

| 评分项 | 占比 | 本项目材料 |
|---|---:|---|
| 需求分析 | 20% | `docs/requirements.md`、用例图、状态图、活动图 |
| 软件设计 | 20% | `docs/design.md`、架构图、ER 图、顺序图、接口表 |
| 系统测试 | 15% | `docs/test-plan-and-cases.md`、`tests/test_services.py` |
| 项目管理 | 15% | `docs/project-management.md`、甘特图、分工和风险表 |
| 程序代码 | 20% | `src/`、`data/`、`tests/` |
| 提交成果完整性 | 10% | `docs/`、`diagrams/`、`src/`、`tests/`、`deliverables/` |
