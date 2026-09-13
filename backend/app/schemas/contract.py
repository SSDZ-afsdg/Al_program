"""
contract.py —— 合同审查相关的 Pydantic 模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class RiskItem(BaseModel):
    """单条风险条款。"""

    # 风险等级：高 / 中 / 低
    level: str = Field(..., description="风险等级：高/中/低")
    # 合同中的原文引用（存在风险的条款片段）
    clause: str = Field(..., description="风险条款原文引用")
    # 风险分析：说明该条款存在什么问题、可能造成什么后果
    analysis: str = Field(..., description="风险分析")
    # 修改建议：给出具体的修改方向或示范表述
    suggestion: str = Field(..., description="修改建议")


class ContractReviewResult(BaseModel):
    """合同审查结果（对应数据库 contracts.review_result JSON 字段）。"""

    # 总体风险等级
    risk_level: str = Field(..., description="总体风险等级：高/中/低")
    # 风险条款列表
    risks: List[RiskItem] = Field(default_factory=list, description="识别出的风险条款列表")
    # 总体审查意见摘要
    summary: str = Field(default="", description="总体审查意见")


class ContractUploadOut(BaseModel):
    """上传合同文件后的输出模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="合同记录ID（后续审查接口使用）")
    file_name: str = Field(..., description="原始文件名")
    # 提取出的文本长度，方便前端展示
    text_length: int = Field(..., description="提取文本的字符数")
    # 文本预览（前 200 字），让用户确认解析是否正确
    text_preview: str = Field(default="", description="合同原文预览（前200字）")


class ContractOut(BaseModel):
    """合同审查历史列表项模型。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="记录ID")
    file_name: str = Field(..., description="原始文件名")
    # 是否已完成审查（review_result 是否为空）
    reviewed: bool = Field(..., description="是否已完成审查")
    # 审查结果：未审查时为 None
    review_result: Optional[Dict[str, Any]] = Field(default=None, description="审查结果")
    created_at: datetime = Field(..., description="上传时间")
