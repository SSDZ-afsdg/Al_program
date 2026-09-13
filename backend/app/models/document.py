"""
document.py —— 文书生成记录模型

对应数据库表：documents
保存用户每次生成法律文书的表单数据与生成结果。

注意：模型类命名为 DocumentRecord，避免与 python-docx 库中的 Document 类冲突。
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentRecord(Base):
    """文书生成记录表 ORM 模型。"""

    __tablename__ = "documents"

    # 主键：自增整型
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="记录ID")

    # 所属用户 ID：外键关联 users.id
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属用户ID",
    )

    # 文书类型：起诉状 / 答辩状 / 律师函 / 授权委托书
    doc_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="文书类型：起诉状/答辩状/律师函/授权委托书"
    )

    # 用户填写的表单数据：以 JSON 结构存储（MySQL 中对应 JSON 类型）
    # 例如起诉状：{"plaintiff": "张三", "defendant": "李四", "claim": "..."}
    form_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="用户填写的表单数据（JSON）"
    )

    # AI 生成的文书正文
    generated_content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="生成的文书内容"
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="创建时间"
    )

    # -------- 关联关系 --------
    # 反向关联到用户对象
    user: Mapped["User"] = relationship(back_populates="documents")

    def __repr__(self) -> str:
        return f"<DocumentRecord(id={self.id}, doc_type={self.doc_type!r})>"
