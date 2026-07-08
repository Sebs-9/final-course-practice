# GitHub 协作说明

## 1. 仓库建议

- 仓库类型：Private。
- 推荐仓库名：`se-final-smart-home`。
- 默认分支：`main`。
- 课程资料仅在组内受控使用，仓库权限按小组协作需要配置。

## 2. 克隆与运行

组员获得仓库权限后执行：

```powershell
git clone https://github.com/<owner>/se-final-smart-home.git
cd se-final-smart-home
python src\run.py
```

测试：

```powershell
python -m unittest discover -s tests -v
```

## 3. 分支规范

每个人从 `main` 拉分支开发：

```powershell
git checkout -b feature/requirements-doc
git checkout -b feature/frontend-dashboard
git checkout -b feature/alert-service
git checkout -b feature/test-cases
git checkout -b docs/presentation
```

建议分支前缀：

- `feature/`：功能开发。
- `docs/`：文档和图表。
- `test/`：测试用例。
- `fix/`：缺陷修复。

## 4. Issue 分工建议

| Issue | 负责人 | 内容 |
|---|---|---|
| 需求分析文档完善 | 需求负责人 | 检查功能需求、非功能需求、用例图 |
| 软件设计文档完善 | 架构负责人 | 检查架构图、ER 图、接口表 |
| 前端界面优化 | 前端负责人 | 调整看板、设备卡片、告警中心 |
| 后端功能检查 | 后端负责人 | 检查登录、设备、告警、录像、语音服务 |
| 测试用例补充 | 测试负责人 | 补充手工测试记录和兼容性测试 |
| 演示材料准备 | 组长/汇报负责人 | PPT、截图、录屏和讲稿 |

## 5. Pull Request 规范

每个 PR 至少说明：

- 做了什么。
- 对应哪个 Issue。
- 如何验证。
- 是否影响演示流程。

合并前建议执行：

```powershell
python -m unittest discover -s tests -v
```

## 6. 提交信息规范

示例：

```text
docs: refine requirements and use cases
feat: add alert linkage service
test: cover voice command parser
fix: reject guest device control
```
