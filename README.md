# 法宝 - AI 法律助手

基于 **Vue 3 + FastAPI + MySQL + FastGPT** 的智能法律服务平台，提供 AI 法律咨询、法律文书生成、合同风险审查三大核心功能。

## ✨ 功能特性

| 模块 | 说明 |
| --- | --- |
| **AI 法律咨询** | 多轮对话式法律咨询，支持流式输出（打字机效果），聊天记录持久化 |
| **文书生成** | 支持起诉状、答辩状、律师函、授权委托书，动态表单 + AI 生成，Markdown 渲染 |
| **合同审查** | 上传 docx/pdf 合同，AI 智能识别高/中/低风险条款并给出法律依据和修改建议 |
| **用户系统** | JWT 注册/登录，数据按用户隔离 |

## 🛠 技术栈

**前端**
- Vue 3 + Vite + Vue Router 4
- Element Plus（UI 组件库）
- Axios（HTTP 请求）
- marked（Markdown 渲染）

**后端**
- Python 3.11+ + FastAPI + Uvicorn
- SQLAlchemy 2.0 + Alembic（数据库迁移）
- PyMySQL（MySQL 驱动）
- Pydantic V2（数据校验）
- python-jose + passlib + bcrypt（JWT 认证与密码加密）
- httpx（异步调用 FastGPT）
- python-docx + PyPDF2（合同文本提取）

**AI 服务**
- FastGPT（本地部署或云服务），三套独立应用分别对应三个功能模块

**数据库**
- MySQL 8.0

## 📋 环境要求

- Node.js ≥ 18
- Python ≥ 3.11
- MySQL ≥ 8.0
- FastGPT（本地部署 或 云服务账号）

## 📁 项目结构

```
alassistant/
├── index.html                  # 前端入口 HTML
├── package.json                # 前端依赖
├── vite.config.js              # Vite 配置（含 /api 代理到后端）
├── src/                        # 前端源码
│   ├── api/                    # API 请求封装
│   ├── assets/styles/          # 全局样式
│   ├── components/             # 公共组件
│   ├── composables/            # 组合式函数（useAuth）
│   ├── router/                 # 路由配置
│   ├── utils/request.js        # Axios 封装（JWT 注入、401 处理）
│   └── views/                  # 页面组件
│       ├── AiConsult.vue       # AI 法律咨询
│       ├── DocGenerate.vue     # 文书生成
│       ├── ContractReview.vue  # 合同审查
│       ├── HomePage.vue        # 首页
│       └── Login.vue           # 登录页
└── backend/                    # 后端源码
    ├── app/
    │   ├── api/                # 路由层（auth/chat/document/contract）
    │   ├── core/               # 核心（安全、依赖、异常）
    │   ├── models/             # 数据模型
    │   ├── schemas/            # Pydantic 校验模型
    │   ├── services/           # 业务服务（含 ai_service.py）
    │   ├── utils/              # 工具（文件解析）
    │   ├── config.py           # 配置管理
    │   ├── database.py         # 数据库连接
    │   └── main.py             # FastAPI 入口
    ├── alembic/                # 数据库迁移
    ├── .env.example            # 环境变量示例
    └── requirements.txt        # Python 依赖
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/SSDZ-afsdg/Al_program.git
cd Al_program
```

### 2. 启动 MySQL 并创建数据库

```sql
CREATE DATABASE fabao DEFAULT CHARSET utf8mb4;
```

### 3. 配置后端环境变量

```bash
cd backend
copy .env.example .env
```

编辑 `backend/.env`，填入你的 MySQL 密码和 FastGPT 配置（见下方「FastGPT 配置」）。

### 4. 安装后端依赖并启动

```bash
cd backend
pip install -r requirements.txt

# 执行数据库迁移（创建表）
alembic upgrade head

# 启动后端服务（端口 8000）
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. 安装前端依赖并启动

```bash
# 在项目根目录
npm install
npm run dev
```

前端启动后访问 http://localhost:5173/

## 🔧 FastGPT 配置

项目使用三套独立的 FastGPT 应用，分别对应三个功能模块。需在 `backend/.env` 中配置：

```env
# AI 法律咨询
FASTGPT_CHAT_BASE_URL=http://localhost:3000      # 你的 FastGPT 地址
FASTGPT_CHAT_API_KEY=fastgpt-xxxxxxxxxxxx        # 应用 API Key
FASTGPT_CHAT_APP_ID=xxxxxxxxxxxxxxxx             # 应用 ID

# 文书生成
FASTGPT_DOC_BASE_URL=http://localhost:3000
FASTGPT_DOC_API_KEY=fastgpt-xxxxxxxxxxxx
FASTGPT_DOC_APP_ID=xxxxxxxxxxxxxxxx

# 合同审查
FASTGPT_CONTRACT_BASE_URL=http://localhost:3000
FASTGPT_CONTRACT_API_KEY=fastgpt-xxxxxxxxxxxx
FASTGPT_CONTRACT_APP_ID=xxxxxxxxxxxxxxxx
```

> **说明**：
> - `BASE_URL` 为 FastGPT 服务地址，本地部署填 `http://localhost:3000`，云服务填 `https://cloud.fastgpt.cn`
> - API Key 在 FastGPT 应用的「发布渠道 → API 访问」中创建（需为**应用特定 Key**，非全局通用 Key）
> - APP_ID 从应用 URL 路径中获取
> - 若某项未配置，对应模块会返回友好提示或降级到本地模板（文书/合同审查）

## 📡 API 接口概览

所有接口前缀 `/api/v1`，统一响应格式 `{ code, message, data }`。

| 模块 | 方法 | 路径 | 说明 |
| --- | --- | --- | --- |
| 认证 | POST | `/auth/register` | 用户注册 |
| 认证 | POST | `/auth/login` | 用户登录（返回 JWT） |
| 对话 | GET/POST | `/chat/conversations` | 对话列表 / 新建对话 |
| 对话 | DELETE | `/chat/conversations/{id}` | 删除对话 |
| 对话 | GET | `/chat/conversations/{id}/messages` | 历史消息 |
| 对话 | POST | `/chat/conversations/{id}/messages/stream` | **流式**发送消息（SSE） |
| 文书 | POST | `/documents/generate` | 生成法律文书 |
| 文书 | GET | `/documents/list` | 文书历史 |
| 合同 | POST | `/contracts/upload` | 上传合同文件 |
| 合同 | POST | `/contracts/review/{id}` | 智能审查合同 |
| 合同 | GET | `/contracts/list` | 审查历史 |

## ❓ 常见问题

**Q: 文书生成/合同审查超时？**
A: 前端 axios 超时已设为 120 秒。若 FastGPT 响应较慢，可在 `src/utils/request.js` 中调大 `timeout`。

**Q: FastGPT 鉴权失败（错误码 514）？**
A: 检查 API Key 是否为「应用特定 Key」（在应用详情页创建），而非账号全局 Key。同时确认 BASE_URL 与 FastGPT 部署地址一致。

**Q: 合同上传后无反应？**
A: 确保文件为 `.docx` 或 `.pdf` 格式。检查后端 `uploads/` 目录是否有写入权限。

**Q: 如何修改数据库连接信息？**
A: 编辑 `backend/.env` 中的 `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`，重启后端即可。

## 📄 License

MIT
