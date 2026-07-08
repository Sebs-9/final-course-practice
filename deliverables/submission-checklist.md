# 材料检查清单

## 文档材料

- [x] 需求分析文档：`docs/requirements.md`
- [x] 软件设计文档：`docs/design.md`
- [x] 测试计划与用例报告：`docs/test-plan-and-cases.md`
- [x] 项目管理文档：`docs/project-management.md`
- [x] 部署与操作说明：`docs/deployment-and-user-guide.md`
- [x] 成员分工与心得：`docs/team-work-and-reflection-template.md`
- [x] 版本管理记录：`docs/version-history.md`

## 图表原始素材

- [x] 用例图：`diagrams/use-case.puml`
- [x] 架构图：`diagrams/architecture.mmd`
- [x] ER 图：`diagrams/er-diagram.mmd`
- [x] 告警顺序图：`diagrams/sequence-alert.puml`
- [x] 语音活动图：`diagrams/activity-voice.mmd`
- [x] 告警状态图：`diagrams/state-alert.mmd`
- [x] 甘特图：`diagrams/gantt.mmd`

## 程序与测试

- [x] 系统入口：`src/run.py`
- [x] 后端代码：`src/smart_home/`
- [x] 前端代码：`src/web/`
- [x] 自动化测试：`tests/test_services.py`
- [x] 接口测试：`tests/test_http_api.py`
- [x] SQLite 数据库：启动后自动生成 `data/smart_home.sqlite`

## 演示材料

- [x] 5 分钟课堂演示提纲：`docs/presentation-outline.md`
- [x] 15 分钟汇报视频脚本：`docs/report-video-script.md`
- [x] 实际界面截图：`assets/dashboard-authenticated.png`、`assets/dashboard-current.png`
- [x] 提交材料索引：`deliverables/submission-materials-index.md`
- [x] 本地服务健康检查：`/health` 返回 `{"status":"ok"}`
- [x] 登录和看板接口检查：admin 账号可返回 5 个房间、9 个设备、3 个摄像头
- [x] DeepSeek 真实连接测试：使用本机代理 `127.0.0.1:7897` 测试通过，密钥采用本地配置和脱敏展示
- [x] 自动化测试：31 个测试通过

## 提交前命令

```powershell
cd path\to\final-course-practice
python -m unittest discover -s tests -v
python src\run.py
```
