"""
config.py —— 全局配置管理模块

使用 pydantic-settings 从项目根目录的 .env 文件读取配置，
并在代码中以类型安全的方式（settings.xxx）访问。

新增配置项时：
1. 在 .env.example 中补充示例；
2. 在本文件的 Settings 类中添加对应字段。
"""

from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# 后端项目根目录（本文件位于 app/config.py，向上两层即为 backend/）
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """全局配置类：字段名与 .env 文件中的变量名一一对应（不区分大小写）。"""

    # -------- 应用基础配置 --------
    APP_NAME: str = "法宝-AI法律助手后端"  # 应用名称
    APP_ENV: str = "development"           # 运行环境
    DEBUG: bool = True                     # 是否开启调试模式

    # -------- MySQL 数据库配置 --------
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "fabao"

    # -------- JWT 认证配置 --------
    JWT_SECRET_KEY: str = "dev-secret-key-please-change"  # JWT 签名密钥
    JWT_ALGORITHM: str = "HS256"                          # JWT 签名算法
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7        # Token 有效期（默认 7 天）

    # -------- 文件上传配置 --------
    UPLOAD_DIR: str = "uploads"                  # 上传文件存放目录（相对路径）
    ALLOWED_EXTENSIONS: str = "docx,pdf"         # 允许的扩展名（逗号分隔的字符串）
    MAX_FILE_SIZE: int = 10 * 1024 * 1024        # 文件大小上限（默认 10MB）

    # -------- 跨域配置 --------
    # 声明为字符串，通过下方校验器转换为列表，方便 .env 中以逗号分隔书写
    CORS_ORIGINS: str = "http://localhost:5173"

    # -------- FastGPT AI 服务配置（三套，分别对应三个功能模块） --------
    # 说明：每个功能模块使用独立的 FastGPT 应用，可分别配置工作流、知识库与提示词。
    # 基础地址、API Key、AppId 三项为一组，留空或填 "your-..." 视为未配置。

    # —— AI法律咨询模块 ——
    FASTGPT_CHAT_BASE_URL: str = "https://cloud.fastgpt.cn"
    FASTGPT_CHAT_API_KEY: str = ""
    FASTGPT_CHAT_APP_ID: str = ""

    # —— 文书生成模块 ——
    FASTGPT_DOC_BASE_URL: str = "https://cloud.fastgpt.cn"
    FASTGPT_DOC_API_KEY: str = ""
    FASTGPT_DOC_APP_ID: str = ""

    # —— 合同审查模块 ——
    FASTGPT_CONTRACT_BASE_URL: str = "https://cloud.fastgpt.cn"
    FASTGPT_CONTRACT_API_KEY: str = ""
    FASTGPT_CONTRACT_APP_ID: str = ""

    @field_validator("DEBUG", mode="before")
    @classmethod
    def _parse_debug(cls, value):
        """
        将 .env 中的字符串布尔值（"true"/"false"）转换为 Python bool。
        pydantic-settings 默认能处理，但显式处理可避免 "false" 被当作真值的隐患。
        """
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on")
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        """将逗号分隔的跨域来源字符串解析为列表（去除空白项）。"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        """
        拼接 SQLAlchemy 所需的数据库连接 URL（同步 PyMySQL 驱动）。

        格式：mysql+pymysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4
        使用 utf8mb4 字符集以完整支持中文及 emoji 存储。
        """
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def upload_path(self) -> Path:
        """上传文件存储目录的绝对路径（基于后端根目录解析）。"""
        return BASE_DIR / self.UPLOAD_DIR

    # pydantic-settings V2 配置：指定 .env 文件位置与编码
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 环境变量名不区分大小写
        extra="ignore"         # 忽略 .env 中未声明的多余变量
    )


# 全局唯一的配置单例：其他模块统一通过 from app.config import settings 引入
settings = Settings()
