"""
schemas 包初始化文件

集中导出各业务模块的 Pydantic 请求/响应模型。
"""

from app.schemas.common import ApiResponse, success_response, error_response
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserOut,
    TokenResponse,
)
from app.schemas.chat import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
)
from app.schemas.document import (
    DocumentGenerateRequest,
    DocumentOut,
    DocumentListItem,
)
from app.schemas.contract import (
    RiskItem,
    ContractReviewResult,
    ContractOut,
    ContractUploadOut,
)

__all__ = [
    "ApiResponse",
    "success_response",
    "error_response",
    "UserCreate",
    "UserLogin",
    "UserOut",
    "TokenResponse",
    "ConversationCreate",
    "ConversationOut",
    "MessageCreate",
    "MessageOut",
    "DocumentGenerateRequest",
    "DocumentOut",
    "DocumentListItem",
    "RiskItem",
    "ContractReviewResult",
    "ContractOut",
    "ContractUploadOut",
]
