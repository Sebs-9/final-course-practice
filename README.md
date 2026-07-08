# 软件工程期末课程实践

## 选题

选题方向一：全屋智能系统

项目暂定名：全屋智能安防与语音控制系统

本项目以“家居视频监控与安防智能系统”为主线，实现多房间设备管理、实时监控模拟、异常报警、录像回放、场景联动和语音指令控制等功能；同时吸收“智能家居语音交互助手系统”的语音交互要求，使原型更完整地体现全屋智能场景。

## 目录

- `docs/`：需求、设计、测试、项目管理等文档。
- `diagrams/`：UML、ER、架构图、甘特图等原始素材。
- `assets/`：截图、演示素材、界面资源。
- `data/`：测试数据、种子数据。
- `src/`：系统原型代码。
- `tests/`：测试代码与测试数据说明。
- `deliverables/`：最终提交包、演示材料、汇报材料。

## 当前审阅点

当前已完成完整项目原型、文档、图表和测试材料。

## 运行

```powershell
cd path\to\final-course-practice
python src\run.py
```

访问：

```text
http://127.0.0.1:8000
```

演示账号：

- 管理员：`admin / Admin@SE2026!`
- 家庭成员：`member / Member@SE2026!`
- 访客查看者：`guest / Guest@SE2026!`

语音指令默认使用本地规则解析。若需要演示 DeepSeek 大模型解析，可在页面“语音与场景”区域保存 DeepSeek API 密钥并测试连接；网络环境需要代理时，先为 Python 进程设置 `HTTP_PROXY` / `HTTPS_PROXY`。

## 测试

```powershell
python -m unittest discover -s tests -v
```

当前结果：31 个测试全部通过。

## 关键文档

- `docs/requirements.md`：需求分析文档。
- `docs/design.md`：软件设计文档。
- `docs/test-plan-and-cases.md`：测试计划与用例报告。
- `docs/project-management.md`：项目管理文档。
- `docs/final-requirement-mapping.md`：与课程考核 PDF 的逐项对应关系。
- `docs/deployment-and-user-guide.md`：部署与操作说明。
- `docs/team-work-and-reflection-template.md`：6 名组员分工与课程实践心得。
- `docs/report-video-script.md`：15 分钟项目汇报视频录制脚本。
- `docs/version-history.md`：真实 Git 版本管理记录。
- `deliverables/submission-materials-index.md`：最终提交材料索引。
