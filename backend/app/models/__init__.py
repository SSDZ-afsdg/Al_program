"""
models 包初始化文件

集中导入所有 ORM 模型，作用：
1. 方便其他模块统一从 app.models 引入（如 from app.models import User）；
2. 保证 SQLAlchemy 的 Base.metadata 能收集到全部表定义
   （Alembic 自动生成迁移、create_all 建表均依赖此点）。
"""

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import DocumentRecord
from app.models.contract import Contract

# __all__ 声明：控制 from app.models import * 时导出的名称
__all__ = [
    "User",
    "Conversation",
    "Message",
    "DocumentRecord",
    "Contract",
]
