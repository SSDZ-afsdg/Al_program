"""
auth.py —— 认证相关接口

路由前缀：/api/v1/auth
接口清单：
- POST   /register      用户注册
- POST   /login         用户登录，返回 JWT
- GET    /me            获取当前登录用户信息（需认证）
- PATCH  /profile       修改当前用户资料（用户名/邮箱/手机号）
- PUT    /password      修改当前用户密码（校验旧密码）
- POST   /avatar        上传/更新当前用户头像
"""

import datetime
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import BizException
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User
from app.schemas.common import success_response
from app.schemas.user import (
    AvatarUploadOut,
    ChangePasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
)

# 创建路由对象，统一前缀与 OpenAPI 分组标签
router = APIRouter(prefix="/auth", tags=["认证模块"])

# 允许的头像图片扩展名（小写，含点）
_ALLOWED_AVATAR_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
# 头像文件大小上限：2MB（头像无需高清大图，限制可避免占用空间）
_MAX_AVATAR_SIZE = 2 * 1024 * 1024


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
    3. 生成 JWT 访问令牌并连同用户信息一起返回；
    4. 刷新 last_login_at 用于个人中心展示。
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

    # 账号被禁用：阻止登录
    if not user.is_active:
        raise BizException(code=403, message="账号已被禁用，请联系管理员")

    # 刷新最近登录时间（UTC 转本地时区简化处理，MySQL 不存时区信息）
    user.last_login_at = datetime.datetime.now()
    db.add(user)
    db.commit()
    db.refresh(user)

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


@router.patch("/profile", summary="修改个人资料")
def update_profile(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    修改个人资料：用户名、邮箱、手机号，全部可选。
    字段唯一性校验：用户名/邮箱不能与他人重复。
    """
    # 逐字段校验并更新，避免一次性覆盖空值
    if payload.username is not None and payload.username != current_user.username:
        # 检查用户名是否已被占用
        existed = db.scalar(select(User).where(User.username == payload.username, User.id != current_user.id))
        if existed:
            raise BizException(code=400, message="用户名已被注册")
        current_user.username = payload.username

    if payload.email is not None and payload.email != current_user.email:
        existed = db.scalar(select(User).where(User.email == payload.email, User.id != current_user.id))
        if existed:
            raise BizException(code=400, message="邮箱已被注册")
        current_user.email = payload.email

    if payload.phone is not None and payload.phone != (current_user.phone or ""):
        current_user.phone = payload.phone or None

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return success_response(
        data=UserOut.model_validate(current_user).model_dump(mode="json"),
        message="资料更新成功",
    )


@router.put("/password", summary="修改密码")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    修改密码：
    1. 校验旧密码是否正确；
    2. 新密码不能与旧密码相同；
    3. 更新哈希入库。
    """
    # 校验旧密码
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise BizException(code=400, message="旧密码不正确")

    # 新旧密码不能相同
    if payload.old_password == payload.new_password:
        raise BizException(code=400, message="新密码不能与旧密码相同")

    # 更新密码哈希
    current_user.hashed_password = hash_password(payload.new_password)
    db.add(current_user)
    db.commit()
    return success_response(message="密码修改成功")


@router.post("/avatar", summary="上传/更新头像")
async def upload_avatar(
    file: UploadFile = File(..., description="头像图片，支持 png/jpg/jpeg/webp/gif"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传或更新当前用户头像：
    1. 校验扩展名与文件大小（≤ 2MB）；
    2. 以 UUID 重命名保存到 avatars 子目录；
    3. 将相对路径写入 user.avatar_url，返回可访问 URL。
    """
    # -------- 1. 校验扩展名 --------
    original_name = file.filename or ""
    suffix = Path(original_name).suffix.lower()
    if suffix not in _ALLOWED_AVATAR_EXTS:
        raise BizException(
            code=400,
            message=f"不支持的图片类型：{suffix or '未知'}，仅支持 png/jpg/jpeg/webp/gif",
        )

    # -------- 2. 读取并校验大小 --------
    content = await file.read()
    if not content:
        raise BizException(code=400, message="上传文件为空")
    if len(content) > _MAX_AVATAR_SIZE:
        raise BizException(code=400, message="头像大小不能超过 2MB")

    # -------- 3. 保存文件 --------
    # 头像统一放到 uploads/avatars 子目录，与合同文件隔离
    avatars_dir = settings.upload_path / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = avatars_dir / stored_name
    saved_path.write_bytes(content)

    # -------- 4. 更新数据库 --------
    # 数据库保存相对路径（相对 backend 根目录），便于迁移
    relative_path = f"{settings.UPLOAD_DIR}/avatars/{stored_name}"
    current_user.avatar_url = relative_path
    db.add(current_user)
    db.commit()

    # 返回前端可直接使用的访问 URL（依赖 main.py 挂载的 /uploads 静态目录）
    avatar_url = f"/{relative_path}"
    data = AvatarUploadOut(avatar_url=avatar_url)
    return success_response(data=data.model_dump(mode="json"), message="头像上传成功")
