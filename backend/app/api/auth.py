"""
auth.py —— 认证相关接口

路由前缀：/api/v1/auth
接口清单：
- POST /register  用户注册
- POST /login     用户登录，返回 JWT
- GET  /me        获取当前登录用户信息（需认证）
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.exceptions import BizException
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas.common import success_response
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserOut
from app.config import settings

# 创建路由对象，统一前缀与 OpenAPI 分组标签
router = APIRouter(prefix="/auth", tags=["认证模块"])


@router.post("/register", summary="用户注册")
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册接口：
    1. 校验用户名/邮箱是否已被注册；
    2. 对明文密码做 bcrypt 哈希后入库；
    3. 返回新用户基本信息。
    """
    # 查询是否已存在相同用户名或邮箱的用户（or_ 表示两个条件满足其一即可）
    existed = db.scalar(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.email)
        )
    )
    if existed is not None:
        # 精确提示是用户名还是邮箱冲突，提升注册体验
        if existed.username == payload.username:
            raise BizException(code=400, message="用户名已被注册")
        raise BizException(code=400, message="邮箱已被注册")

    # 创建用户对象（密码只保存哈希值）
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    # 提交事务，写入数据库
    db.commit()
    # 刷新对象，获取自增主键 id 与默认时间字段
    db.refresh(user)

    # 返回统一响应结构，data 中为用户信息
    return success_response(data=UserOut.model_validate(user).model_dump(), message="注册成功")


@router.post("/login", summary="用户登录")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录接口：
    1. 支持使用用户名或邮箱登录；
    2. 校验密码哈希；
    3. 生成 JWT 访问令牌并连同用户信息一起返回。
    """
    # 按用户名或邮箱查找账号
    user = db.scalar(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.username)
        )
    )

    # 用户不存在或密码错误，统一返回模糊提示（避免泄露账号是否存在）
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise BizException(code=status.HTTP_401_UNAUTHORIZED, message="用户名或密码错误")

    # 生成 JWT：sub 放用户 ID，额外附带用户名
    access_token = create_access_token(
        subject=user.id,
        extra_claims={"username": user.username},
    )

    # 组装符合 TokenResponse 结构的数据
    data = TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )
    return success_response(data=data.model_dump(mode="json"), message="登录成功")


@router.get("/me", summary="获取当前用户信息")
def me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户信息。
    依赖 get_current_user：请求必须携带有效的 Bearer Token，否则返回 401。
    """
    return success_response(data=UserOut.model_validate(current_user).model_dump())
