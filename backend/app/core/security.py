"""
security.py —— 安全认证核心工具

包含两部分能力：
1. 密码哈希：基于 passlib + bcrypt，提供加密与校验；
2. JWT 令牌：基于 python-jose，提供访问令牌的生成与解析。
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import UnauthorizedException

# -------- 密码哈希 --------

# CryptContext：passlib 的统一加密上下文
# schemes 指定使用 bcrypt 算法；deprecated="auto" 表示自动处理旧算法的迁移
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    对明文密码进行 bcrypt 哈希。

    :param plain_password: 用户注册时提交的明文密码
    :return: 可入库存储的密码哈希字符串
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    校验明文密码与数据库中的哈希是否匹配。

    :param plain_password: 登录时提交的明文密码
    :param hashed_password: 数据库中保存的密码哈希
    :return: 匹配返回 True，否则返回 False
    """
    return pwd_context.verify(plain_password, hashed_password)


# -------- JWT 令牌 --------

def create_access_token(
    subject: str | int,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    """
    生成 JWT 访问令牌。

    :param subject: 令牌主体（通常为用户 ID 的字符串形式），写入标准字段 sub
    :param extra_claims: 需要额外写入令牌的自定义声明（如用户名）
    :param expires_minutes: 有效期（分钟），不传则使用全局配置
    :return: 编码后的 JWT 字符串
    """
    # 计算过期时间：当前 UTC 时间 + 有效时长
    # 注意：必须显式从 datetime 引入 timedelta（不可用 datetime.timedelta）
    expire_delta = timedelta(
        minutes=expires_minutes if expires_minutes is not None
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    expire = datetime.now(timezone.utc) + expire_delta

    # 组装载荷（Payload）
    payload: Dict[str, Any] = {
        "sub": str(subject),     # 主体：用户ID
        "exp": expire,           # 过期时间（jose 会自动校验）
        "iat": datetime.now(timezone.utc),  # 签发时间
    }
    # 合并额外声明
    if extra_claims:
        payload.update(extra_claims)

    # 使用密钥与算法签名生成令牌
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    解析并验证 JWT 令牌。

    :param token: 前端请求头携带的 JWT 字符串
    :return: 解码后的载荷字典
    :raises UnauthorizedException: 令牌无效、过期或签名错误时抛出 401 异常
    """
    try:
        # 解码时会自动校验签名与过期时间
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        # JWTError 涵盖签名错误、过期、格式错误等全部解析失败场景
        raise UnauthorizedException(f"登录凭证无效或已过期：{exc}") from exc
