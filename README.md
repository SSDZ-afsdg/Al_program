# 法宝 - AI 法律助手

基于 **Vue 3 + FastAPI + MySQL + FastGPT** 的智能法律服务平台，提供 AI 法律咨询、法律文书生成、合同风险审查三大核心功能。

## ✨ 功能特性

| 模块 | 说明 |
| --- | --- |
| **AI 法律咨询** | 多轮对话式法律咨询，SSE 流式输出（打字机效果）；左侧会话列表支持新建/切换/**重命名**/删除，历史消息**游标分页**加载（滚动锚定不跳动） |
| **文书生成** | 支持起诉状、答辩状、律师函、授权委托书，动态表单 + AI 生成，Markdown 渲染；一键**导出排版规范的 Word 文档**（仿宋正文、首行缩进、标题居中） |
| **合同审查** | 上传 docx/pdf 合同，AI 智能识别高/中/低风险条款并给出法律依据和修改建议；**风险条款在合同原文中三色定位高亮**，点击即可跳转闪烁定位；支持**导出 PDF 审查报告** |
| **个人中心** | 头像上传（≤2MB）、用户名/邮箱/手机号修改、密码修改（含旧密码校验与新旧密码差异化校验）；**使用统计首页**展示对话数、消息数、文书数、合同数与**近 7 天活跃趋势柱状图** |
| **用户系统** | JWT 注册/登录，数据按用户隔离；登录刷新 `last_login_at`；账号禁用拦截 |

## 🛠 技术栈

**前端**
- Vue 3 + Vite + Vue Router 4
- Element Plus（UI 组件库）
- Axios（HTTP 请求）
- marked + DOMPurify（Markdown 渲染 + XSS 清洗，自动给 a 链接追加 `target=_blank` 与 `rel=noopener`）

**后端**
- Python 3.11+ + FastAPI + Uvicorn
- SQLAlchemy 2.0 + Alembic（数据库迁移）
- PyMySQL（MySQL 驱动）
- Pydantic V2（数据校验）
- python-jose + passlib + bcrypt（JWT 认证与密码加密）
- httpx（异步调用 FastGPT）
- python-docx + PyPDF2（合同文本提取 / Word 文书生成导出）
- reportlab（合同审查报告 PDF 生成，自动适配系统中文字体）

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
│   │   ├── auth.js            # 认证 + 个人中心（注册/登录/资料修改/密码修改/头像上传）
│   │   ├── chat.js             # AI 咨询
│   │   ├── contract.js         # 合同审查
│   │   ├── document.js         # 文书生成
│   │   └── stats.js            # 使用统计
│   ├── assets/styles/          # 全局样式
│   ├── components/             # 公共组件
│   ├── composables/            # 组合式函数（useAuth）
│   ├── router/                 # 路由配置
│   ├── utils/request.js        # Axios 封装（JWT 注入、401 处理、blob 直通）
│   ├── utils/download.js       # 文件下载工具（Word/PDF 导出、中文文件名解析）
│   ├── utils/markdown.js       # Markdown 渲染工具（marked + DOMPurify XSS 清洗）
│   └── views/                  # 页面组件
│       ├── AiConsult.vue       # AI 法律咨询（会话管理 + 消息分页 + SSE 流式）
│       ├── DocGenerate.vue     # 文书生成（Markdown 渲染 + Word 导出）
│       ├── ContractReview.vue  # 合同审查（风险原文高亮定位 + PDF 报告导出）
│       ├── HomePage.vue        # 首页
│       ├── Login.vue           # 登录页
│       └── Profile.vue         # 个人中心（资料/密码/头像 + 使用统计）
└── backend/                    # 后端源码
    ├── app/
    │   ├── api/                # 路由层
    │   │   ├── auth.py             # 认证 + 个人中心（注册/登录/资料/密码/头像）
    │   │   ├── chat.py             # AI 咨询
    │   │   ├── contract.py         # 合同审查
    │   │   ├── document.py         # 文书生成
    │   │   └── stats.py            # 使用统计
    │   ├── core/               # 核心（安全、依赖、异常）
    │   ├── models/             # 数据模型
    │   ├── schemas/            # Pydantic 校验模型
    │   ├── services/           # 业务服务（含 ai_service.py）
    │   ├── utils/              # 工具
    │   │   ├── file_handler.py       # 合同文件文本提取
    │   │   ├── markdown_to_docx.py    # Markdown 转排版规范的 Word
    │   │   └── pdf_report.py          # 合同审查报告 PDF 生成
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
| 认证 | POST | `/auth/login` | 用户登录（返回 JWT，刷新 `last_login_at`） |
| 认证 | GET | `/auth/me` | 获取当前用户信息（含头像/手机号/角色/最近登录时间） |
| 认证 | PATCH | `/auth/profile` | 修改个人资料（用户名/邮箱/手机号，唯一性校验排除自身） |
| 认证 | PUT | `/auth/password` | 修改密码（旧密码校验，新旧不能相同） |
| 认证 | POST | `/auth/avatar` | 上传头像（png/jpg/jpeg/webp/gif，≤2MB；存 `uploads/avatars/`，UUID 重命名） |
| 统计 | GET | `/stats/summary` | 当前用户使用统计（对话/消息/文书/合同数 + 近 7 天活跃趋势） |
| 对话 | GET/POST | `/chat/conversations` | 对话列表 / 新建对话 |
| 对话 | PATCH | `/chat/conversations/{id}` | 重命名对话 |
| 对话 | DELETE | `/chat/conversations/{id}` | 删除对话 |
| 对话 | GET | `/chat/conversations/{id}/messages` | 历史消息（游标分页：`limit`、`before_id`，返回 `items`+`has_more`） |
| 对话 | POST | `/chat/conversations/{id}/messages/stream` | **流式**发送消息（SSE） |
| 文书 | POST | `/documents/generate` | 生成法律文书 |
| 文书 | GET | `/documents/list` | 文书历史 |
| 文书 | GET | `/documents/{id}` | 文书详情 |
| 文书 | GET | `/documents/{id}/export` | **导出 Word（.docx）文件下载** |
| 合同 | POST | `/contracts/upload` | 上传合同文件 |
| 合同 | POST | `/contracts/review/{id}` | 智能审查合同 |
| 合同 | GET | `/contracts/list` | 审查历史 |
| 合同 | GET | `/contracts/{id}` | 合同详情（含原文全文，供风险高亮定位） |
| 合同 | GET | `/contracts/{id}/export-pdf` | **导出审查报告 PDF 下载** |

> 文件导出接口返回二进制流（`responseType: 'blob'`），中文文件名通过 `Content-Disposition: filename*=UTF-8''` 编码，前端统一由 `src/utils/download.js` 处理保存。

## 📖 核心功能使用说明

**AI 法律咨询**
- 点击左侧「新建对话」开始咨询，会话列表显示标题与最近更新时间；
- 鼠标悬停会话项可「重命名 / 删除」；
- 历史消息默认加载最新 20 条，顶部「加载更早的消息」按需翻页，新消息发送后会话自动置顶。

**文书生成**
- 左侧选择文书类型并填写动态表单，点击「生成文书」后显示带进度条的加载动画；
- 结果以 Markdown 排版渲染，可一键复制或点击「下载 Word」获得排版规范的 .docx 文件（仿宋正文、首行缩进两字符、标题居中）。

**合同审查**
- 上传 docx/pdf → 点击「开始智能审查」，等待 AI 输出风险评级与逐条分析；
- 审查完成后，左侧自动展示「合同原文（风险高亮）」：高/中/低风险条款分别以红/橙/绿三色标记，点击风险卡片右上角的定位图标可跳转到原文对应位置并闪烁提示；
- 点击右侧「导出审查报告 PDF」下载带风险徽章、条款详情和免责声明的正式报告。

**个人中心**
- 顶部用户卡片：点击头像即可上传新头像（≤2MB，UUID 重命名存至 `uploads/avatars/`）；展示用户名、邮箱、手机号、角色、注册时间、最近登录时间。
- 使用统计区：4 个数字卡片（对话数、消息数、文书数、合同数），下方为近 7 天活跃趋势柱状图（纯 CSS 实现，无第三方图表库依赖）；活跃事件综合对话/消息/文书/合同创建按日期聚合。
- 修改个人资料：用户名/邮箱/手机号单独可选提交，后端做唯一性校验时排除当前用户自身；手机号必须 11 位数字。
- 修改密码：旧密码错误会拦截，新旧密码不能相同，修改成功后建议重新登录。

## ❓ 常见问题

**Q: 文书生成/合同审查超时？**
A: 前端 axios 超时已设为 120 秒。若 FastGPT 响应较慢，可在 `src/utils/request.js` 中调大 `timeout`。

**Q: FastGPT 鉴权失败（错误码 514）？**
A: 检查 API Key 是否为「应用特定 Key」（在应用详情页创建），而非账号全局 Key。同时确认 BASE_URL 与 FastGPT 部署地址一致。

**Q: 合同上传后无反应？**
A: 确保文件为 `.docx` 或 `.pdf` 格式。检查后端 `uploads/` 目录是否有写入权限。

**Q: 如何修改数据库连接信息？**
A: 编辑 `backend/.env` 中的 `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`，重启后端即可。

**Q: 数据库迁移如何执行？**
A: 在 `backend/` 目录执行 `alembic upgrade head`。当前已包含两次迁移：
- `0001_initial`：创建 users / conversations / messages / documents / contracts 五张核心表
- `0002_user_profile`：为 users 表扩展 `avatar_url`、`phone`、`is_active`、`role`、`last_login_at` 字段（个人中心所需）

**Q: 导出审查报告 PDF 提示"未找到可用的中文字体"？**
A: PDF 生成依赖系统中文字体（Windows/macOS 自带）。Linux 服务器执行：

```bash
# Debian / Ubuntu
apt-get update && apt-get install -y fonts-noto-cjk

# CentOS / RHEL
yum install -y google-noto-sans-cjk-fonts
```

安装后无需重启即可生效（程序在每次生成时探测字体）。

**Q: 合同风险条款在原文中没有高亮？**
A: 高亮依赖 AI 返回的「原文引用」与合同提取文本的匹配。系统已内置去空白归一化匹配（兼容 PDF 提取换行打断的情况），若 AI 引用与原文差异过大仍可能无法定位，此时不影响右侧风险分析与 PDF 报告导出。

## 📝 更新日志

**v1.2.0（2026-09-14）**
- ✨ 个人中心：新增 `Profile.vue` 页面，路由 `/profile`，AppHeader 下拉菜单加入口
- ✨ 后端用户中心接口：`PATCH /auth/profile`（用户名/邮箱/手机号，唯一性校验排除自身）、`PUT /auth/password`（旧密码校验，新旧差异化）、`POST /auth/avatar`（png/jpg/jpeg/webp/gif，≤2MB，UUID 重命名存 `uploads/avatars/`）
- ✨ User 模型扩展：`avatar_url`、`phone`、`is_active`、`role`（user/admin）、`last_login_at`；新增 `0002_user_profile_fields` 迁移；登录成功时刷新 `last_login_at`，账号禁用时拦截
- ✨ 使用统计：新增 `GET /stats/summary` 接口与 `src/api/stats.js`，返回对话/消息/文书/合同数 + 近 7 天每日活跃事件聚合（前端展示 4 个数字卡片 + 纯 CSS 柱状图，无第三方图表依赖）
- 🔧 安全增强：安装 `dompurify`，新建 `src/utils/markdown.js` 统一封装 `renderMarkdown`（marked 解析 + DOMPurify XSS 清洗，afterSanitizeAttributes 钩子自动给 a 标签追加 `target=_blank` 与 `rel=noopener noreferrer`）；`AiConsult.vue`、`DocGenerate.vue` 全部切换到新工具，覆盖所有 AI 返回内容 v-html 场景
- 🔧 useAuth 增加 `setUser` 用于本地用户信息更新；上传头像 API 走 multipart 由 axios 自动处理 boundary（沿用项目惯例，避免丢失 boundary）

**v1.1.0（2026-09-13）**
- ✨ AI 咨询：新增会话重命名（PATCH 接口）；历史消息改为游标分页加载，加载更早消息时滚动位置锚定不跳动；会话列表展示更新时间并支持操作按钮悬停浮现
- ✨ 文书生成：新增 Word 导出接口，Markdown 转 .docx（黑体标题居中、仿宋正文、首行缩进、1.5 倍行距），前端「下载」升级为「下载 Word」
- ✨ 合同审查：新增合同详情接口（返回原文全文）；风险条款在原文中按高/中/低三色高亮定位，支持点击跳转与闪烁动画；新增 reportlab PDF 审查报告导出（风险徽章、条款详情、免责声明）
- 🔧 前端 axios 支持 blob 响应直通，新增统一文件下载工具 `utils/download.js`
- 🔧 requirements.txt 新增 reportlab==4.2.5

**v1.0.0**
- 🎉 项目初始化：AI 法律咨询（SSE 流式）、法律文书生成、合同智能审查三大模块，JWT 用户体系 + FastGPT 三套应用接入

## 📄 License

MIT
