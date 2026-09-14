"""
user.py —— 用户相关的 Pydantic 模型

包含：注册请求、登录请求、用户信息输出、登录令牌响应、
      用户资料更新、密码修改请求、头像上传响应、使用统计输出。
Pydantic V2 使用 model_config / field_validator 等新式 API。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """用户注册请求体。"""

    # 用户名：3~50 字符
    username: str = Field(..., min_length=3, max_length=50, description="用户名（3~50个字符）")
    # 邮箱：使用 EmailStr 自动校验邮箱格式（依赖 email-validator 库）
    email: EmailStr = Field(..., description="邮箱地址")
    # 密码：至少 6 位（注册时为明文，服务端只保存其哈希值）
    password: str = Field(..., min_length=6, max_length=64, description="密码（至少6位）")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """校验用户名：去除首尾空格，不允许包含空白字符。"""
        value = value.strip()
        if any(ch.isspace() for ch in value):
            raise ValueError("用户名不能包含空格")
        return value


class UserLogin(BaseModel):
    """用户登录请求体（JSON 方式，便于前端调用）。"""

    # 登录账号：用户名或邮箱均可，由服务端自行判断
    username: str = Field(..., description="用户名或邮箱")
    # 登录密码（明文传输，生产环境需使用 HTTPS）
    password: str = Field(..., description="密码")


class UserOut(BaseModel):
    """用户信息输出模型：返回给前端时绝不能携带密码字段。"""

    # 启用从 ORM 对象属性读取（Pydantic V2 替代旧版 orm_mode 的写法）
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    avatar_url: Optional[str] = Field(default=None, description="头像URL")
    phone: Optional[str] = Field(default=None, description="手机号")
    role: str = Field(default="user", description="角色")
    last_login_at: Optional[datetime] = Field(default=None, description="最近登录时间")
    created_at: datetime = Field(..., description="注册时间")


class TokenResponse(BaseModel):
    """登录成功后返回的 JWT 令牌数据。"""

    # JWT 访问令牌
    access_token: str = Field(..., description="JWT 访问令牌")
    # 令牌类型，固定为 Bearer，前端请求头格式：Authorization: Bearer <token>
    token_type: str = Field(default="bearer", description="令牌类型")
    # 令牌有效期（秒），方便前端做过期判断
    expires_in: Optional[int] = Field(default=None, description="令牌有效期（秒）")
    # 登录用户的基本信息
    user: UserOut = Field(..., description="用户信息")


class UserUpdate(BaseModel):
    """用户资料更新请求体（个人中心修改昵称/邮箱/手机号）。

    所有字段均为可选，只更新前端提交的字段，避免覆盖未提交项。
    """

    username: Optional[str] = Field(default=None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=20, description="手机号")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: Optional[str]) -> Optional[str]:
        """校验用户名：去除首尾空格，不允许包含空白字符。"""
        if value is None:
            return value
        value = value.strip()
        if any(ch.isspace() for ch in value):
            raise ValueError("用户名不能包含空格")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        """校验手机号格式：允许为空，非空时只允许 11 位数字（中国大陆手机号）。"""
        if value is None or value == "":
            return None
        value = value.strip()
        if not value.isdigit() or len(value) != 11:
            raise ValueError("手机号必须为 11 位数字")
        return value


class ChangePasswordRequest(BaseModel):
    """修改密码请求体：需要校验旧密码，提交新密码。"""

    # 旧密码：服务端与数据库哈希比对
    old_password: str = Field(..., description="旧密码")
    # 新密码：至少 6 位，与旧密码不能相同（差异化校验在路由层做）
    new_password: str = Field(..., min_length=6, max_length=64, description="新密码（至少6位）")


class AvatarUploadOut(BaseModel):
    """头像上传成功后返回的数据。"""

    # 头像访问 URL（前端可直接拼接 baseURL 后用于 <img src>)
    avatar_url: str = Field(..., description="头像访问URL")


class UserStatsOut(BaseModel):
    """用户使用统计输出模型。"""

    # 对话总数
    conversation_count: int = Field(default=0, description="对话总数")
    # 消息总数（含用户与 AI）
    message_count: int = Field(default=0, description="消息总数")
    # 文书生成总数
    document_count: int = Field(default=0, description="文书生成总数")
    # 合同上传总数
    contract_count: int = Field(default=0, description="合同上传总数")
    # 已完成审查的合同数
    reviewed_contract_count: int = Field(default=0, description="已审查合同数")
    # 最近 7 天每日活跃次数（用于绘制趋势图）
    recent_activity: list = Field(default_factory=list, description="近7天活跃数据")
