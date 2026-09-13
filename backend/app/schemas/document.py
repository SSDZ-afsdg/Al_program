"""
document.py —— 文书生成相关的 Pydantic 模型
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator

# 系统当前支持的四种文书类型
SUPPORTED_DOC_TYPES = ("起诉状", "答辩状", "律师函", "授权委托书")


class DocumentGenerateRequest(BaseModel):
    """文书生成请求体。"""

    # 文书类型：必须属于支持的四种之一
    doc_type: str = Field(..., description="文书类型：起诉状/答辩状/律师函/授权委托书")
    # 表单数据：键值对形式，不同文书类型所需字段不同，由服务层按模板取用
    form_data: Dict[str, Any] = Field(
        default_factory=dict, description="用户填写的表单数据（键值对）"
    )

    @field_validator("doc_type")
    @classmethod
    def validate_doc_type(cls, value: str) -> str:
        """校验文书类型是否在支持范围内。"""
        value = value.strip()
        if value not in SUPPORTED_DOC_TYPES:
            raise ValueError(f"不支持的文书类型：{value}，当前仅支持：{ '、'.join(SUPPORTED_DOC_TYPES) }")
        return value


class DocumentOut(BaseModel):
    """单条文书记录的完整输出模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    user_id: int = Field(..., description="所属用户ID")
    doc_type: str = Field(..., description="文书类型")
    form_data: Dict[str, Any] = Field(..., description="生成时填写的表单数据")
    generated_content: str = Field(..., description="生成的文书正文")
    created_at: datetime = Field(..., description="生成时间")


class DocumentListItem(BaseModel):
    """文书历史列表项模型（列表场景不返回冗长的正文）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    doc_type: str = Field(..., description="文书类型")
    # 截取正文前 100 字作为预览
    content_preview: str = Field(default="", description="文书正文预览（前100字）")
    created_at: datetime = Field(..., description="生成时间")
