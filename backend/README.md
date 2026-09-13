# 法宝 - AI法律助手（后端）

基于 **FastAPI + SQLAlchemy 2.0 + MySQL + Alembic + Pydantic V2** 的后端服务，
为前端提供 AI 法律咨询、法律文书生成、合同智能审查三大模块的 API。

## 一、技术栈

| 技术 | 版本/说明 |
| --- | --- |
| Python | 3.11+ |
| FastAPI | Web 框架（自动生成 Swagger 文档） |
| SQLAlchemy | 2.0（新式 `DeclarativeBase` + `Mapped` 声明式写法） |
| Alembic | 数据库迁移 |
| PyMySQL | MySQL 同步驱动 |
| Pydantic | V2（请求/响应数据校验） |
| python-jose | JWT 令牌生成与校验 |
| passlib + bcrypt | 密码哈希 |
| python-multipart | 文件上传 |
| python-docx / PyPDF2 | 解析 .docx / .pdf 合同文本 |
| uvicorn | ASGI 服务器 |

## 二、目录结构

```
backend/
├── app/
│   ├── main.py                 # 应用入口：CORS、异常处理、路由注册
│   ├── config.py               # 配置管理（读取 .env）
│   ├── database.py             # 引擎、会话工厂、声明式基类
│   ├── models/                 # SQLAlchemy 模型（5 张表）
│   ├── schemas/                # Pydantic 请求/响应模型 + 统一响应
│   ├── api/                    # 路由层（auth/chat/document/contract）
│   ├── services/               # 业务逻辑层（AI、文书、合同审查）
│   ├── core/                   # 安全(JWT/密码)、依赖注入、异常处理
│   └── utils/                  # 文件解析工具
├── alembic/                    # 迁移目录（versions 下放迁移脚本）
├── uploads/                    # 合同上传文件存储目录
├── alembic.ini                 # Alembic 配置
├── requirements.txt            # 依赖清单
├── .env.example                # 环境变量示例
└── README.md
```

## 三、环境要求

- Python 3.11 及以上
- MySQL 5.7 及以上（推荐 MySQL 8.0），账号具备建库建表权限

## 四、安装步骤

> 以下命令均在 `backend/` 目录下执行。

### 1. 创建并激活虚拟环境

```bash
# 创建虚拟环境
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

# Linux / macOS
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 创建 MySQL 数据库

登录 MySQL 后执行（数据库名需与 `.env` 中 `DB_NAME` 一致）：

```sql
CREATE DATABASE fabao DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 配置环境变量

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

然后编辑 `.env`，按本地 MySQL 实际情况修改 `DB_USER`、`DB_PASSWORD`、`DB_PORT` 等配置；
生产环境务必修改 `JWT_SECRET_KEY` 为足够复杂的随机字符串。

## 五、数据库初始化（Alembic 迁移）

项目已内置初始迁移脚本（创建 users、conversations、messages、documents、contracts 五张表），
执行迁移即可建表：

```bash
# 升级到最新版本（创建全部表）
alembic upgrade head

# 查看迁移历史
alembic history

# 回退一个版本
alembic downgrade -1
```

> 以后修改 ORM 模型后，生成新迁移的流程：
> ```bash
> alembic revision --autogenerate -m "本次变更说明"
> alembic upgrade head
> ```

## 六、启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：

- 服务根地址（健康检查）：<http://localhost:8000/>
- **Swagger 接口文档（可在线调试）**：<http://localhost:8000/docs>
- ReDoc 文档：<http://localhost:8000/redoc>

## 七、API 总览

所有接口统一前缀 `/api/v1`，统一响应结构：

```json
{ "code": 200, "message": "success", "data": {} }
```

| 模块 | 方法 | 路径 | 鉴权 | 说明 |
| --- | --- | --- | --- | --- |
| 认证 | POST | `/api/v1/auth/register` | 否 | 用户注册 |
| 认证 | POST | `/api/v1/auth/login` | 否 | 登录获取 JWT |
| 认证 | GET | `/api/v1/auth/me` | 是 | 当前用户信息 |
| 咨询 | GET | `/api/v1/chat/conversations` | 是 | 对话列表 |
| 咨询 | POST | `/api/v1/chat/conversations` | 是 | 新建对话 |
| 咨询 | DELETE | `/api/v1/chat/conversations/{id}` | 是 | 删除对话 |
| 咨询 | GET | `/api/v1/chat/conversations/{id}/messages` | 是 | 消息列表 |
| 咨询 | POST | `/api/v1/chat/conversations/{id}/messages` | 是 | 发送消息（返回 AI 回复） |
| 文书 | POST | `/api/v1/documents/generate` | 是 | 生成文书 |
| 文书 | GET | `/api/v1/documents/list` | 是 | 文书历史 |
| 文书 | GET | `/api/v1/documents/{id}` | 是 | 文书详情 |
| 合同 | POST | `/api/v1/contracts/upload` | 是 | 上传 .docx/.pdf |
| 合同 | POST | `/api/v1/contracts/review/{id}` | 是 | 执行风险审查 |
| 合同 | GET | `/api/v1/contracts/list` | 是 | 审查历史 |

### 鉴权方式

登录成功后，在后续请求头中携带 JWT：

```
Authorization: Bearer <access_token>
```

## 八、当前阶段说明

- AI 法律咨询回复、合同风险审查均为**模拟数据**，相关接入点已在
  `app/services/ai_service.py`、`app/services/contract_service.py` 中以
  `# TODO` 注释标明，替换内部实现即可接入真实大模型；
- 文书生成使用本地字符串模板（起诉状/答辩状/律师函/授权委托书）。
