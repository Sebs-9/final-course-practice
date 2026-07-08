# 版本管理记录

## 1. 说明

项目使用 Git 进行版本管理，主要代码和文档保存在 `feature/deepseek-voice-command` 分支。本记录用于说明项目迭代过程，提交记录来自当前项目仓库。

## 2. 当前分支

```text
feature/deepseek-voice-command
```

## 3. 主要提交记录

```text
d63cf9c docs: use provided member work summary
7c42f3d chore: address final evaluation feedback
08d813f docs: complete submission materials
0bb9299 fix: reset alarm after resolving alerts
9fac1ed feat: add DeepSeek voice command integration
f52eeae Polish smart home dashboard UI (#3)
a47d986 Add living room visual demo (#2)
f657153 Fix dashboard navigation and static encoding
61a91a5 Initial smart home security course project
```

## 4. 迭代说明

| 阶段 | 代表提交 | 主要内容 |
|---|---|---|
| 初始原型 | `61a91a5` | 建立全屋智能安防系统基础代码、文档和数据结构。 |
| 编码修复 | `f657153` | 修复看板导航和静态资源编码问题。 |
| 可视化增强 | `a47d986`、`f52eeae` | 增强客厅可视化演示和工作台界面。 |
| 智能语音增强 | `9fac1ed` | 增加 DeepSeek 语音指令解析，同时保留本地规则兜底。 |
| 缺陷修复 | `0bb9299` | 修复告警确认处理后警报器未恢复待命的问题。 |
| 提交材料整理 | `08d813f` | 补齐 6 人分工、心得、视频脚本、材料索引和当前截图。 |
| 评估建议整改 | `7c42f3d` | 根据评估报告完善密码盐配置、自动化规则加载、测试覆盖和需求对照说明。 |
| 成员分工更新 | `d63cf9c` | 按小组提供的成员分工资料更新项目管理文档和成员心得材料。 |

## 5. 提交前验证

最终整理前执行：

```powershell
python -m unittest discover -s tests -v
```

当前结果：31 个自动化测试通过。
