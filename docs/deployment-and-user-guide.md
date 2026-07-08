# 部署与操作说明

## 1. 运行环境

- Windows
- Python 3.10 或更高版本
- 现代浏览器：Chrome 或 Edge

项目不需要安装第三方 Python 包，不需要 Node.js，不需要真实摄像头或智能硬件。

## 2. 启动系统

在项目根目录执行：

```powershell
cd path\to\final-course-practice
python src\run.py
```

默认访问地址：

```text
http://127.0.0.1:8000
```

首次启动时，系统会自动创建 SQLite 数据库：

```text
data/smart_home.sqlite
```

## 3. 演示账号

| 角色 | 用户名 | 密码 | 权限 |
|---|---|---|---|
| 管理员 | admin | Admin@SE2026! | 查看日志、控制设备、处理告警、触发模拟事件 |
| 家庭成员 | member | Member@SE2026! | 控制设备、处理告警、语音指令、场景切换 |
| 访客查看者 | guest | Guest@SE2026! | 查看看板和录像，不能控制设备 |

## 4. 推荐演示流程

1. 使用 `admin/Admin@SE2026!` 登录系统。
2. 展示监控总览，包括房间数、设备数、在线设备和多摄像头模拟画面。
3. 在设备控制区域打开客厅灯或启动警报器。
4. 在告警中心模拟“玄关入侵”或“厨房烟雾”。
5. 展示告警生成、录像记录和联动结果。
6. 点击“确认处理”关闭告警。
7. 在语音输入框执行：
   - `打开客厅灯`
   - `查看客厅摄像头`
   - `启动离家安防`
   - `模拟厨房烟雾`
8. 在录像回放中搜索 `厨房`。
9. 展示管理员审计日志。
10. 切换到 `guest/Guest@SE2026!`，展示访客无法控制设备。

## 5. 运行测试

在项目根目录执行：

```powershell
python -m unittest discover -s tests -v
```

当前测试结果：

```text
Ran 29 tests in 6.909s
OK
```

## 6. DeepSeek 语音解析测试

系统默认不依赖外部大模型，语音指令会使用本地规则解析。若需要演示 DeepSeek 解析能力：

1. 启动系统并使用管理员或家庭成员登录。
2. 在“语音与场景”区域输入 DeepSeek API 密钥并保存。
3. 点击“测试连接”，成功后页面会显示当前模型。
4. 输入“帮我把客厅灯打开”等自然语言指令，系统会优先使用 DeepSeek 输出受控动作；若 DeepSeek 失败，则回退到本地规则。

如当前网络访问 DeepSeek 需要本机代理，可在启动服务前设置：

```powershell
$env:HTTP_PROXY="http://127.0.0.1:7897"
$env:HTTPS_PROXY="http://127.0.0.1:7897"
python src\run.py
```

## 7. 目录说明

| 目录 | 内容 |
|---|---|
| `docs/` | 软件工程文档 |
| `diagrams/` | UML、ER、架构图、甘特图等原始素材 |
| `src/` | 系统源代码 |
| `src/web/` | 前端页面、样式和交互脚本 |
| `src/smart_home/` | 后端业务代码 |
| `data/` | SQLite 数据库 |
| `tests/` | 自动化测试 |
| `deliverables/` | 最终提交检查材料 |

## 8. 常见问题

### 端口被占用

使用其他端口启动：

```powershell
python src\run.py --port 8010
```

### 需要重置演示数据

停止服务后删除：

```text
data/smart_home.sqlite
```

然后重新启动系统，数据库会自动重建并写入种子数据。

### 浏览器显示旧状态

刷新页面，或退出登录后重新登录。
