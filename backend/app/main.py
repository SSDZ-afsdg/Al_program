"""
main.py —— FastAPI 应用入口

职责：
1. 创建 FastAPI 应用实例；
2. 注册 CORS 中间件（允许前端 Vue 开发服务器跨域访问）；
3. 注册全局异常处理器（统一响应结构）；
4. 注册各业务路由（统一 /api/v1 前缀）；
5. 挂载上传文件静态目录、提供健康检查接口。

启动方式（在 backend 目录下执行）：
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, chat, contract, document
from app.config import settings
from app.core.exceptions import register_exception_handlers

# -------- 创建应用实例 --------
app = FastAPI(
    title=settings.APP_NAME,
    description="法宝 - AI法律助手后端服务：提供认证、AI法律咨询、文书生成、合同审查接口",
    version="1.0.0",
    docs_url="/docs",        # Swagger UI 文档地址（开发调试用）
    redoc_url="/redoc",      # ReDoc 文档地址
)

# -------- 注册 CORS 中间件 --------
# 前端 Vue（Vite 默认 5173 端口）与后端不同源，必须显式允许跨域
app.add_middleware(
    CORSMiddleware,
    # 允许的来源列表（从 .env 的 CORS_ORIGINS 读取）
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,     # 允许携带 Cookie / 认证信息
    allow_methods=["*"],        # 允许所有 HTTP 方法
    allow_headers=["*"],        # 允许所有请求头
)

# -------- 注册全局异常处理器 --------
# 使业务异常、HTTP 异常、参数校验异常均返回统一的 {code, message, data} 结构
register_exception_handlers(app)

# -------- 注册业务路由 --------
# 所有接口统一挂载到 /api/v1 前缀下，便于后续版本管理
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)       # 认证模块 /api/v1/auth
app.include_router(chat.router, prefix=API_PREFIX)       # AI咨询模块 /api/v1/chat
app.include_router(document.router, prefix=API_PREFIX)   # 文书模块 /api/v1/documents
app.include_router(contract.router, prefix=API_PREFIX)   # 合同模块 /api/v1/contracts

# -------- 挂载上传文件静态目录 --------
# 使上传的合同文件可通过 /uploads/文件名 直接访问（如需要）
settings.upload_path.mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory=str(settings.upload_path)),
    name="uploads",
)


# -------- 健康检查接口 --------
@app.get("/", tags=["系统"], summary="服务健康检查")
def health_check():
    """根路径健康检查，用于快速确认后端服务是否正常运行。"""
    return {
        "code": 200,
        "message": "success",
        "data": {
            "service": settings.APP_NAME,
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
        },
    }
