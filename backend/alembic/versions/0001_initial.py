"""init: 创建用户、对话、消息、文书、合同五张初始表

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-12

说明：本迁移为项目初始迁移，手写创建全部 5 张业务表，
      结构与 app/models 下的 ORM 模型一一对应。
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
# revision：当前版本号；down_revision：上一版本号（初始迁移为 None）
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级：按外键依赖顺序依次创建 5 张表。"""

    # ------------------------------------------------------------------
    # 1. users 用户表（无外键依赖，最先创建）
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="用户ID"),
        sa.Column("username", sa.String(length=50), nullable=False, comment="用户名"),
        sa.Column("email", sa.String(length=100), nullable=False, comment="邮箱"),
        sa.Column("hashed_password", sa.String(length=255), nullable=False, comment="密码哈希值"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        # 用户名与邮箱的唯一约束
        sa.UniqueConstraint("username", name="uk_users_username"),
        sa.UniqueConstraint("email", name="uk_users_email"),
        mysql_charset="utf8mb4",  # 整表使用 utf8mb4，支持中文与 emoji
        mysql_engine="InnoDB",    # InnoDB 支持事务与外键
    )
    # 为用户名、邮箱建立索引（模型中 index=True）
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    # ------------------------------------------------------------------
    # 2. conversations 对话表（外键依赖 users）
    # ------------------------------------------------------------------
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="对话ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="所属用户ID"),
        sa.Column("title", sa.String(length=100), nullable=False, comment="对话标题"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",  # 删除用户时级联删除对话
            name="fk_conversations_user_id",
        ),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    # ------------------------------------------------------------------
    # 3. messages 消息表（外键依赖 conversations）
    # ------------------------------------------------------------------
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="消息ID"),
        sa.Column("conversation_id", sa.Integer(), nullable=False, comment="所属对话ID"),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            comment="消息角色：user-用户，assistant-AI助手",
        ),
        sa.Column("content", sa.Text(), nullable=False, comment="消息内容"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            comment="创建时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",  # 删除对话时级联删除消息
            name="fk_messages_conversation_id",
        ),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    # ------------------------------------------------------------------
    # 4. documents 文书生成记录表（外键依赖 users）
    # ------------------------------------------------------------------
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="记录ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="所属用户ID"),
        sa.Column(
            "doc_type",
            sa.String(length=20),
            nullable=False,
            comment="文书类型：起诉状/答辩状/律师函/授权委托书",
        ),
        # JSON 类型：MySQL 5.7+ 原生支持
        sa.Column("form_data", sa.JSON(), nullable=False, comment="用户填写的表单数据（JSON）"),
        sa.Column("generated_content", sa.Text(), nullable=False, comment="生成的文书内容"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            comment="创建时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_documents_user_id",
        ),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    # ------------------------------------------------------------------
    # 5. contracts 合同审查记录表（外键依赖 users）
    # ------------------------------------------------------------------
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="记录ID"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="所属用户ID"),
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="原始文件名"),
        sa.Column("file_path", sa.String(length=500), nullable=False, comment="服务器文件存储路径"),
        sa.Column("original_text", sa.Text(), nullable=False, comment="提取的合同原文"),
        # 审查结果允许为空：刚上传时尚未执行审查
        sa.Column(
            "review_result",
            sa.JSON(),
            nullable=True,
            comment="审查结果（风险等级与风险条款列表）",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
            comment="创建时间",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_contracts_user_id",
        ),
        mysql_charset="utf8mb4",
        mysql_engine="InnoDB",
    )
    op.create_index("ix_contracts_user_id", "contracts", ["user_id"])


def downgrade() -> None:
    """回滚：按与创建相反的顺序删除全部表（先删依赖方，后删被依赖方）。"""
    op.drop_index("ix_contracts_user_id", table_name="contracts")
    op.drop_table("contracts")

    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
