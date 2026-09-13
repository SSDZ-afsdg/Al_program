"""
alembic/env.py —— Alembic 迁移执行环境配置

关键作用：
1. 把后端根目录加入 sys.path，使迁移脚本可以 import app 包；
2. 从项目的 .env 配置中读取数据库地址，覆盖 alembic.ini 的占位值；
3. 导入全部 ORM 模型，让 target_metadata 收集到完整表结构，
   从而支持 autogenerate（自动生成迁移脚本）。
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# ------------------------------------------------------------------
# 1. 路径处理：将 backend 根目录加入 sys.path
#    本文件位于 backend/alembic/env.py，向上两级即为 backend/
# ------------------------------------------------------------------
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# ------------------------------------------------------------------
# 2. 导入项目配置与模型
# ------------------------------------------------------------------
from app.config import settings  # noqa: E402  （路径注入后才能导入，位置不能上移）
from app.database import Base    # noqa: E402
# 导入 models 包会连带加载全部模型类，使其注册到 Base.metadata
import app.models  # noqa: E402,F401

# Alembic 配置对象（解析 alembic.ini）
config = context.config

# 用 .env 中的真实数据库连接串覆盖 ini 中的占位地址
config.set_main_option("sqlalchemy.url", settings.database_url)

# 配置日志（alembic.ini 中定义了日志格式）
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 迁移目标元数据：autogenerate 时据此与数据库现状做差异比对
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式：生成 SQL 脚本而不连接数据库。

    使用方式：alembic upgrade head --sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,  # 将参数直接内联为字面量，生成可独立执行的 SQL
        dialect_opts={"paramstyle": "named"},
        # 以下两个选项让 MySQL 下的迁移更规范
        compare_type=True,   # 比对列类型变化
        compare_server_default=True,  # 比对默认值变化
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在线模式：连接数据库并直接执行迁移（最常用的方式）。
    """
    # 创建迁移专用引擎（与应用运行时引擎互不影响）
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # 迁移是一次性任务，使用 NullPool 避免连接残留
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Alembic 根据是否带 --sql 参数自动选择离线/在线模式
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
