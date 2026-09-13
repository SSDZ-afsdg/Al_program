"""
contract_service.py —— 合同审查业务逻辑

优先调用 FastGPT「合同审查」应用进行智能风险审查；
若 FastGPT 未配置或返回结果不合法，则降级到本地规则 + 模拟数据，保证前端可展示。
"""

import re
from typing import Dict, List, Optional

from app.services.ai_service import review_contract_via_fastgpt

# 风险等级常量
RISK_HIGH = "高"
RISK_MEDIUM = "中"
RISK_LOW = "低"


def _find_clause(original_text: str, keywords: List[str], fallback: str) -> str:
    """
    在合同原文中按关键词检索相关条款片段。

    实现思路：按句号、分号、换行切分句子，找出第一句包含任一关键词的句子；
    找不到则返回兜底文案。

    :param original_text: 合同全文
    :param keywords: 关键词列表（命中任意一个即可）
    :param fallback: 未命中时的兜底引用文案
    :return: 风险条款原文引用
    """
    # 按中文句号、分号、换行切分成条款句子（保留有内容的片段）
    sentences = [s.strip() for s in re.split(r"[。；\n]", original_text) if s.strip()]
    for sentence in sentences:
        if any(keyword in sentence for keyword in keywords):
            # 找到后补回句号，保持引用完整
            return sentence + "。"
    return fallback


def _review_contract_local(original_text: str) -> Dict:
    """
    本地兜底审查（FastGPT 未配置时使用）。

    以规则 + 模拟数据的方式返回固定的高/中/低三条风险条款。
    """
    # -------- 模拟风险条款（高/中/低各一条） --------

    # 1) 高风险：违约责任不对等（尝试从原文检索"违约"相关条款作为引用）
    high_clause = _find_clause(
        original_text,
        keywords=["违约", "赔偿"],
        fallback="（未在合同中检索到明确的违约责任条款）",
    )
    high_risk = {
        "level": RISK_HIGH,
        "clause": high_clause,
        "analysis": (
            "该条款关于违约责任的约定缺失或明显不对等，可能导致一方违约时"
            "守约方难以主张充分赔偿，发生争议时举证与索赔成本较高。"
        ),
        "suggestion": (
            "建议补充明确、对等的违约责任条款，约定违约金的计算方式或比例，"
            "并明确损失赔偿范围（包括维权产生的律师费、诉讼费等）。"
        ),
    }

    # 2) 中风险：争议解决方式不明确（检索"争议""管辖"关键词）
    medium_clause = _find_clause(
        original_text,
        keywords=["争议", "管辖", "仲裁"],
        fallback="（未在合同中检索到明确的争议解决条款）",
    )
    medium_risk = {
        "level": RISK_MEDIUM,
        "clause": medium_clause,
        "analysis": (
            "争议解决方式（诉讼/仲裁）或管辖法院约定不明，发生纠纷时可能面临"
            "管辖权异议，增加维权的时间与经济成本。"
        ),
        "suggestion": (
            "建议明确约定由合同签订地或己方所在地有管辖权的人民法院诉讼解决，"
            "或明确指定仲裁委员会仲裁（注意诉讼与仲裁只能二选一）。"
        ),
    }

    # 3) 低风险：通知与送达条款不规范（检索"通知""送达"关键词）
    low_clause = _find_clause(
        original_text,
        keywords=["通知", "送达"],
        fallback="（未在合同中检索到通知与送达条款）",
    )
    low_risk = {
        "level": RISK_LOW,
        "clause": low_clause,
        "analysis": (
            "合同缺少规范的通知与送达条款，后续催告、解约通知等可能因"
            "无法证明已有效送达而影响权利行使。"
        ),
        "suggestion": (
            "建议增加通知送达条款，明确双方联系人、地址、邮箱/手机号，"
            "并约定上述信息变更的告知义务及按原地址送达即视为有效。"
        ),
    }

    # -------- 汇总审查结果 --------
    result = {
        "risk_level": RISK_HIGH,
        "summary": (
            "本次审查共识别出 3 处风险条款，其中高风险 1 项、中风险 1 项、低风险 1 项。"
            "建议在签署前重点完善违约责任与争议解决条款。"
            "（当前为本地兜底审查结果，配置 FastGPT 后可获得更智能的审查。）"
        ),
        "risks": [high_risk, medium_risk, low_risk],
    }
    return result


async def review_contract(original_text: str) -> Dict:
    """
    对合同原文执行风险审查。

    优先调用 FastGPT「合同审查」应用；若未配置或返回结果不合法，降级到本地规则。

    :param original_text: 从合同文件中提取的纯文本
    :return: 审查结果字典，结构对应 schemas/contract.py 的 ContractReviewResult
    """
    # 1) 优先调用 FastGPT
    ai_result = await review_contract_via_fastgpt(original_text)
    if ai_result:
        return ai_result

    # 2) 降级到本地规则审查
    return _review_contract_local(original_text)
