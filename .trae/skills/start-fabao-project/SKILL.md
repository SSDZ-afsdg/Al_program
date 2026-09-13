---
name: "start-fabao-project"
description: "一键启动法宝AI法律助手项目的前后端服务（Vite前端5173 + FastAPI后端8000 + MySQL）。当用户说运行项目、启动项目、打开项目、启动前后端、start project 时调用。"
---

# 一键启动法宝项目（start-fabao-project）

在 Windows 环境下启动"法宝 - AI法律助手"全栈项目：Vue 3 + Vite 前端、FastAPI 后端、MySQL 数据库，并完成就绪验证与页面打开。

## 项目位置与关键路径

- 工作区根目录（前端）：`e:\Programs\trac\1\alassistant`
- 后端目录：`e:\Programs\trac\1\alassistant\backend`
- 前端地址：http://localhost:5173/
- 后端地址：http://localhost:8000/ （Swagger 文档：http://localhost:8000/docs）
- MySQL：127.0.0.1:3306，数据库 `fabao`（root/123456，配置在 backend/.env）

## 环境要点（本机已验证，勿随意更换）

- 系统默认 `python` 是 3.9，且 `py -3.14` 启动器注册损坏（指向不存在的 E:\python.exe），**禁止使用**。
- 后端依赖安装在 conda 环境 `fabao`（Python 3.11），解释器绝对路径：
  `E:\Python3.14\Anconda\.conda\envs\fabao\python.exe`
- 前端 node_modules 已安装，直接 `npm run dev` 即可。
- 所有命令通过 Shell 工具执行时必须设置 `dangerouslyDisableSandbox: true`（conda/网络访问需要）。

## 标准执行流程

### 第 1 步：检查服务现状（避免重复启动占用端口）

用 Shell 工具（PowerShell）执行：

```powershell
try { $fe = (Invoke-WebRequest -Uri "http://localhost:5173/" -UseBasicParsing -TimeoutSec 3).StatusCode } catch { $fe = "DOWN" }
try { $be = (Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -UseBasicParsing -TimeoutSec 3).StatusCode } catch { $be = "DOWN" }
Write-Output "frontend(5173): $fe"; Write-Output "backend(8000): $be"
```

仅启动状态为 DOWN 的服务；两个都在运行则直接跳到第 4 步。

### 第 2 步：（按需）启动后端

后台运行（`run_in_background: true`），cwd 必须是 backend 目录：

```powershell
& "E:\Python3.14\Anconda\.conda\envs\fabao\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如用户需要后端热重载，把命令改为加 `--reload`。

### 第 3 步：（按需）启动前端

后台运行（`run_in_background: true`），cwd 必须是工作区根目录：

```powershell
npm run dev
```

### 第 4 步：等待就绪并验证（关键，不可省略）

- 启动后等待约 6~10 秒（前端 Vite 约 6 秒，后端约 3~6 秒）。
- 读取后台任务 output.log 确认：
  - 前端出现 `VITE v6.x ready` 与 `Local: http://localhost:5173/`
  - 后端出现 `Application startup complete.` 与 `Uvicorn running on http://0.0.0.0:8000`
- 再次用 Invoke-WebRequest 确认两个端口均返回 **200**，未就绪则继续等待或排查日志。

### 第 5 步：打开预览并汇报

- 调用 OpenPreview 打开 `http://localhost:5173/`（command_id 用前端后台任务的 ID）。
- 用表格向用户汇报：前端、后端、MySQL 三个服务的地址与状态，以及 Swagger 文档入口。

## 常见故障处理

| 现象 | 处理方式 |
| --- | --- |
| 后端报 `Can't connect to MySQL server` / `Access denied` | 确认 MySQL 服务已启动；用后端解释器执行 pymysql 连接测试；检查 backend/.env 的 DB_* 配置 |
| 后端报表不存在 | 在 backend 目录用 fabao 环境执行：`<fabao-python> -m alembic upgrade head` |
| 端口被占用（10048/address already in use） | 先按第 1 步探测，若旧进程异常占用，告知用户并经确认后结束占用进程，再启动 |
| 前端 `vite 不是内部命令` / 缺依赖 | 在根目录执行 `npm install`（需关闭沙箱），完成后重新 `npm run dev` |
| 前端能打开但接口报错 | 检查后端是否 200；后端 CORS 已放行 5173；当前前端页面尚未对接 API（三个功能页为占位页） |

## 停止服务

- 前端、后端均以后台任务方式运行：用 StopCommand 传入对应 command_id 停止；
- 或告知用户关闭对应终端 / 结束占用 5173、8000 端口的进程。

## 注意事项

- 不要重建 conda 环境、不要重新 npm install（除非依赖确实缺失）。
- 不要改动 .env 中的 JWT 密钥与数据库配置，除非用户明确要求。
- 常驻服务务必后台启动，并向用户说明服务会持续运行、如何停止。
