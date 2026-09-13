"""
exceptions.py —— 自定义业务异常与全局异常处理器

设计目标：让全站接口无论成功或失败，都返回统一的 JSON 结构：
    {"code": xxx, "message": "...", "data": ...}

使用方式：
    # 在路由/服务中主动抛出业务异常
    raise BizException(code=400, message="用户名已存在")

    # 资源不存在的快捷方式
    raise NotFoundException("对话不存在")
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import error_response


class BizException(Exception):
    """
    业务异常基类。

    :param code: 业务错误码（同时作为 HTTP 状态码返回，如 400/401/403/404）
    :param message: 错误提示信息
    :param data: 附加数据
    """

    def __init__(self, code: int = 400, message: str = "业务处理失败", data=None):
        self.code = code
        self.message = message
        self.data = data
        # 调用父类构造，保证异常信息链完整
        super().__init__(message)


class NotFoundException(BizException):
    """资源不存在异常（404）。"""

    def __init__(self, message: str = "请求的资源不存在"):
        super().__init__(code=404, message=message)


class UnauthorizedException(BizException):
    """未认证/认证失效异常（401）。"""

    def __init__(self, message: str = "未登录或登录已过期"):
        super().__init__(code=401, message=message)


class ForbiddenException(BizException):
    """无权限访问异常（403）。"""

    def __init__(self, message: str = "无权访问该资源"):
        super().__init__(code=403, message=message)


def register_exception_handlers(app: FastAPI) -> None:
    """
    向 FastAPI 应用注册全局异常处理器。

    覆盖三类异常：
    1. BizException：自定义业务异常；
    2. StarletteHTTPException：框架抛出的 HTTP 异常（如 404 路由不存在、401）；
    3. RequestValidationError：请求参数校验失败（Pydantic 校验错误）。
    """

    @app.exception_handler(BizException)
    async def handle_biz_exception(request: Request, exc: BizException):
        """处理自定义业务异常：HTTP 状态码与业务码保持一致。"""
        return JSONResponse(
            status_code=exc.code,
            content=error_response(code=exc.code, message=exc.message, data=exc.data),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        """处理框架 HTTP 异常，统一包装为业务响应结构（避免直接返回裸的 {"detail": ...}）。"""
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(code=exc.status_code, message=str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError):
        """
        处理请求参数校验异常（422）。
        提取第一条错误信息作为提示，完整错误明细放入 data 中，便于前端定位字段。
        """
        # exc.errors() 是一个错误字典列表，每项包含 loc/type/msg 等
        errors = exc.errors()
        first_msg = "参数校验失败"
        if errors:
            # loc 形如 ("body", "username")，取最后一段作为出错字段名
            field = errors[0].get("loc", [])[-1] if errors[0].get("loc") else ""
            first_msg = f"参数 {field} 校验失败：{errors[0].get('msg', '')}".strip()
        return JSONResponse(
            status_code=422,
            content=error_response(code=422, message=first_msg, data=errors),
        )
