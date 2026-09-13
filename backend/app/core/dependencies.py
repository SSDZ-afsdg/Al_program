"""
dependencies.py —— FastAPI 公共依赖模块

集中管理各路由共用的依赖项：
- get_db：数据库会话（定义在 database.py，这里转出方便统一引用）
- oauth2_scheme：从 Authorization 请求头提取 Bearer Token
- get_current_user：解析令牌并返回当前登录用户对象（鉴权核心依赖）
"""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db
from app.models import User

# OAuth2 密码流令牌提取器
# tokenUrl 仅用于 OpenAPI 文档的"Authorize"按钮提示，不影响实际接口逻辑
# 前端只需在请求头携带：Authorization: Bearer <access_token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前登录用户的依赖函数。

    执行链路：
    1. oauth2_scheme 从请求头提取 Bearer Token（缺失时框架自动返回 401）；
    2. decode_access_token 校验签名与有效期，得到载荷中的用户 ID；
    3. 根据用户 ID 查询数据库，返回 User 对象。

    使用方式（路由函数参数中声明即可完成鉴权）：
        current_user: User = Depends(get_current_user)

    :raises UnauthorizedException: 令牌无效或用户不存在时抛出 401
    """
    # 解析令牌载荷
    payload = decode_access_token(token)

    # 从标准声明 sub 中取出用户 ID
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("令牌缺少用户标识")

    # 查询用户是否仍然存在（防止令牌有效但用户已被删除的情况）
    user = db.scalar(select(User).where(User.id == int(user_id_str)))
    if user is None:
        raise UnauthorizedException("用户不存在或已被注销")

    return user
