"""
conversation.py —— 对话模型

对应数据库表：conversations
一个用户可以拥有多个对话，每个对话包含多条消息（一对多关系）。
"""

from datetime import datetime
from typing import List

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Conversation(Base):
    """对话表 ORM 模型：AI 法律咨询的会话容器。"""

    __tablename__ = "conversations"

    # 主键：自增整型
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="对话ID")

    # 所属用户 ID：外键关联 users.id
    # ondelete="CASCADE"：数据库层面保证删除用户时连带删除其对话
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,  # 按用户查询对话是高频操作，建立索引
        comment="所属用户ID",
    )

    # 对话标题：最长 100 字符，新建时可用首条消息摘要作为标题
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="对话标题")

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="创建时间"
    )

    # 更新时间：有新消息时随记录更新自动刷新
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )

    # -------- 关联关系 --------
    # 反向关联到用户对象
    user: Mapped["User"] = relationship(back_populates="conversations")

    # 该对话下的所有消息，随对话删除而级联删除
    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",  # 消息固定按创建时间正序排列
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title!r})>"
