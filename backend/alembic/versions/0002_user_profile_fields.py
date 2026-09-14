"""add user profile fields: avatar_url, phone, is_active, role, last_login_at

Revision ID: 0002_user_profile
Revises: 0001_initial
Create Date: 2026-09-14

说明：为 users 表扩展用户中心所需字段：
      - avatar_url：头像 URL
      - phone：手机号
      - is_active：账号启用状态
      - role：角色（user/admin）
      - last_login_at：最近登录时间
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_user_profile"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级：为 users 表新增 5 个字段。均允许为空或有默认值，不会破坏现有数据。"""
    # 头像 URL：可空，存储相对路径或完整 URL
    op.add_column("users", sa.Column("avatar_url", sa.String(length=500), nullable=True, comment="头像URL"))
    # 手机号：可空
    op.add_column("users", sa.Column("phone", sa.String(length=20), nullable=True, comment="手机号"))
    # 账号启用状态：默认 True（历史用户全部视为启用）
    op.add_column("users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1", comment="账号是否启用"))
    # 角色：默认 user
    op.add_column("users", sa.Column("role", sa.String(length=20), nullable=False, server_default="user", comment="角色：user/admin"))
    # 最近登录时间：可空
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(), nullable=True, comment="最近登录时间"))


def downgrade() -> None:
    """回滚：按添加相反顺序删除字段。"""
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "role")
    op.drop_column("users", "is_active")
    op.drop_column("users", "phone")
    op.drop_column("users", "avatar_url")
