"""
common.py —— 统一响应模型与响应构造工具

全站所有接口统一返回如下 JSON 结构：
{
    "code": 200,
    "message": "success",
    "data": { ... }
}
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

# 泛型类型变量：使 ApiResponse 可以携带任意类型的 data
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应模型（泛型），可用于 OpenAPI 文档的响应结构声明。"""

    # 业务状态码：200 成功，其他值表示各类错误
    code: int = 200
    # 提示信息：成功为 "success"，失败时为具体错误原因
    message: str = "success"
    # 业务数据：成功时返回具体数据，失败时通常为 None
    data: Optional[T] = None


def success_response(data: Any = None, message: str = "success") -> dict:
    """
    构造成功响应字典。

    :param data: 要返回给前端的业务数据
    :param message: 提示信息，默认 "success"
    :return: 统一结构的响应字典
    """
    return {"code": 200, "message": message, "data": data}


def error_response(code: int, message: str, data: Any = None) -> dict:
    """
    构造失败响应字典。

    :param code: 业务错误码（如 400、401、404）
    :param message: 错误提示信息
    :param data: 附加数据（一般为 None）
    :return: 统一结构的响应字典
    """
    return {"code": code, "message": message, "data": data}
