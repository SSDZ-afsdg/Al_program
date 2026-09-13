"""
database.py —— 数据库连接与会话管理

基于 SQLAlchemy 2.0 同步引擎（PyMySQL 驱动）：
- engine：全局数据库连接引擎（连接池）
- SessionLocal：数据库会话工厂
- Base：所有 ORM 模型的声明式基类（2.0 新式 DeclarativeBase 写法）
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


# 创建数据库引擎
# pool_pre_ping=True：每次从连接池取连接前先做一次心跳检测，
#   避免 MySQL 默认 8 小时断开空闲连接后出现 "MySQL server has gone away" 错误
# pool_recycle=3600：连接最长存活 1 小时后自动回收，刷新连接池
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,  # 调试模式下打印实际执行的 SQL，方便排查问题
)

# 会话工厂：每次调用 SessionLocal() 都会产生一个独立的数据库会话
# autocommit=False / autoflush=False：显式控制事务提交与 flush，符合 Web 开发最佳实践
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # 提交后对象属性不过期，避免提交后再次访问触发额外查询
)


class Base(DeclarativeBase):
    """
    所有 ORM 模型的声明式基类。

    SQLAlchemy 2.0 推荐写法：继承 DeclarativeBase，
    各模型再继承本类并使用 Mapped[] / mapped_column() 声明字段。
    """
    pass


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖函数（供 FastAPI 依赖注入使用）。

    使用方式：
        @app.get("/")
        def index(db: Session = Depends(get_db)):
            ...

    执行流程：
    1. 请求开始时创建一个数据库会话；
    2. yield 将会话交给路由函数使用；
    3. 请求结束（无论成功或异常）后关闭会话，归还连接到连接池。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # 确保任何情况下会话都被关闭，防止连接泄漏
        db.close()
