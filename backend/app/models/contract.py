"""
contract.py —— 合同审查记录模型

对应数据库表：contracts
保存用户上传的合同文件信息、提取出的合同原文以及 AI 审查结果。
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contract(Base):
    """合同审查记录表 ORM 模型。"""

    __tablename__ = "contracts"

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

    # 上传文件的原始文件名
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="原始文件名"
    )

    # 文件在服务器上的实际存储路径（绝对或相对路径）
    file_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="服务器文件存储路径"
    )

    # 从文件中提取的合同纯文本原文
    original_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="提取的合同原文"
    )

    # 审查结果：JSON 结构，包含总体风险等级与风险条款列表
    # 上传时为空（None），执行审查后回写；故允许为空
    # 结构示例：
    # {
    #   "risk_level": "高",
    #   "risks": [
    #     {"level": "高", "clause": "原文引用", "analysis": "风险分析", "suggestion": "修改建议"}
    #   ]
    # }
    review_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None, comment="审查结果（风险等级与风险条款列表）"
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, comment="创建时间"
    )

    # -------- 关联关系 --------
    # 反向关联到用户对象
    user: Mapped["User"] = relationship(back_populates="contracts")

    def __repr__(self) -> str:
        return f"<Contract(id={self.id}, file_name={self.file_name!r})>"
