"""
message.py —— 消息模型

对应数据库表：messages
存储一个对话中的每一条消息，role 字段区分消息发送方：
- "user"      ：用户发送的消息
- "assistant" ：AI 助手回复的消息
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Message(Base):
    """消息表 ORM 模型。"""

    __tablename__ = "messages"

    # 主键：自增整型
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="消息ID")

    # 所属对话 ID：外键关联 conversations.id
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # 按对话拉取消息列表是高频操作，建立索引
        comment="所属对话ID",
    )

    # 消息角色：仅允许 "user" / "assistant" 两种取值
    # 按需求使用 String(20) 存储，业务层负责取值合法性校验
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="消息角色：user-用户，assistant-AI助手"
    )

    # 消息正文：Text 类型不限长度，可容纳长文本
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="创建时间"
    )

    # -------- 关联关系 --------
    # 反向关联到所属对话
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role!r})>"
