"""
user.py —— 用户模型

对应数据库表：users
存储用户账号信息（用户名、邮箱、加密后的密码、头像、手机号、角色等）。
"""

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """用户表 ORM 模型。"""

    # 数据库表名
    __tablename__ = "users"

    # 主键：自增整型
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")

    # 用户名：唯一索引，最长 50 字符，不允许为空
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )

    # 邮箱：唯一索引，最长 100 字符，不允许为空
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False, comment="邮箱"
    )

    # 密码哈希值：只存哈希不存明文，长度预留 255
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希值"
    )

    # 头像 URL：可空，用户未上传时为 None；存储相对路径或完整 URL
    avatar_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None, comment="头像URL"
    )

    # 手机号：可空，支持后续绑定；最长 20 字符
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None, comment="手机号"
    )

    # 账号状态：True 启用 / False 禁用（管理员可禁用违规账号）
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="账号是否启用"
    )

    # 角色：user 普通用户 / admin 管理员（为后续管理后台预留）
    role: Mapped[str] = mapped_column(
        String(20), default="user", nullable=False, comment="角色：user/admin"
    )

    # 最近登录时间：登录成功时刷新，可空（注册后从未登录的情况）
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, default=None, comment="最近登录时间"
    )

    # 创建时间：由数据库端 CURRENT_TIMESTAMP 生成默认值
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="创建时间"
    )

    # 更新时间：默认当前时间，记录更新时由数据库自动刷新为当前时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )

    # -------- 关联关系（SQLAlchemy 2.0 新式类型标注） --------
    # 该用户创建的所有对话；cascade 配置为随用户删除级联清理
    conversations: Mapped[List["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",  # 删除用户时一并删除其对话
        lazy="selectin",  # selectin 预加载：查询用户时顺带查出对话，避免 N+1
    )

    # 该用户的文书生成记录
    documents: Mapped[List["DocumentRecord"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # 该用户的合同审查记录
    contracts: Mapped[List["Contract"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """对象的可读表示，便于日志与调试输出。"""
        return f"<User(id={self.id}, username={self.username!r})>"
