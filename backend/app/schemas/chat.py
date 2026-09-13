"""
chat.py —— AI 法律咨询（对话/消息）相关的 Pydantic 模型
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    """新建对话请求体（标题可不传，默认给一个标题）。"""

    # 对话标题：可选，最长 100 字符
    title: Optional[str] = Field(
        default=None, max_length=100, description="对话标题，不传则使用默认标题"
    )


class MessageCreate(BaseModel):
    """发送消息请求体。"""

    # 用户发送的消息内容：不允许为空串
    content: str = Field(..., min_length=1, description="用户提问内容")


class MessageOut(BaseModel):
    """单条消息输出模型。"""

    # 允许从 ORM 对象自动转换
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="所属对话ID")
    role: str = Field(..., description="角色：user / assistant")
    content: str = Field(..., description="消息内容")
    created_at: datetime = Field(..., description="发送时间")


class ConversationOut(BaseModel):
    """对话输出模型（对话列表、新建对话返回均使用此模型）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="对话ID")
    user_id: int = Field(..., description="所属用户ID")
    title: str = Field(..., description="对话标题")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ChatReplyOut(BaseModel):
    """发送消息后的响应：包含用户消息与 AI 回复消息（消息列表）。"""

    # 用户消息（已落库）
    user_message: MessageOut = Field(..., description="用户消息")
    # AI 回复消息（已落库）
    assistant_message: MessageOut = Field(..., description="AI回复消息")
