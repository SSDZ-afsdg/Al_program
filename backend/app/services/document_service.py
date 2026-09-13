"""
document_service.py —— 文书生成业务逻辑

优先调用 FastGPT「文书生成」应用生成专业法律文书；
若 FastGPT 未配置，则降级使用本地字符串模板拼接，保证功能可用。
"""

from typing import Any, Dict

from app.core.exceptions import BizException
from app.services.ai_service import generate_document_via_fastgpt

# 支持的四种文书类型（与 schemas/document.py 中保持一致）
DOC_TYPE_LAWSUI = "起诉状"
DOC_TYPE_DEFENSE = "答辩状"
DOC_TYPE_LETTER = "律师函"
DOC_TYPE_POWER = "授权委托书"


def _get_value(form_data: Dict[str, Any], key: str, default: str = "（未填写）") -> str:
    """
    安全地从表单字典中取值。

    :param form_data: 用户提交的表单数据
    :param key: 字段名
    :param default: 字段缺失或为空时的占位文本
    :return: 字符串形式的字段值
    """
    value = form_data.get(key)
    # None、空字符串、纯空白均视为未填写
    if value is None or str(value).strip() == "":
        return default
    return str(value)


def _generate_lawsuit(form_data: Dict[str, Any]) -> str:
    """生成《民事起诉状》文本。"""
    return f"""民 事 起 诉 状

原告：{_get_value(form_data, "plaintiff")}
性别：{_get_value(form_data, "plaintiff_gender")}
身份证号：{_get_value(form_data, "plaintiff_id_card")}
住址：{_get_value(form_data, "plaintiff_address")}
联系电话：{_get_value(form_data, "plaintiff_phone")}

被告：{_get_value(form_data, "defendant")}
住址/住所地：{_get_value(form_data, "defendant_address")}
联系电话：{_get_value(form_data, "defendant_phone")}

诉讼请求：
{_get_value(form_data, "claim")}

事实与理由：
{_get_value(form_data, "facts")}

综上所述，为维护原告的合法权益，特向贵院提起诉讼，恳请依法判决。

此致
{_get_value(form_data, "court")}人民法院

具状人（签名）：{_get_value(form_data, "plaintiff")}
{_get_value(form_data, "date")}
"""


def _generate_defense(form_data: Dict[str, Any]) -> str:
    """生成《民事答辩状》文本。"""
    return f"""民 事 答 辩 状

答辩人（被告）：{_get_value(form_data, "respondent")}
住址/住所地：{_get_value(form_data, "respondent_address")}
联系电话：{_get_value(form_data, "respondent_phone")}

因 {_get_value(form_data, "plaintiff")} 诉答辩人 {_get_value(form_data, "case_reason")} 一案，
现提出答辩意见如下：

{_get_value(form_data, "defense")}

综上所述，请求人民法院依法查明事实，驳回原告的诉讼请求。

此致
{_get_value(form_data, "court")}人民法院

答辩人（签名）：{_get_value(form_data, "respondent")}
{_get_value(form_data, "date")}
"""


def _generate_lawyer_letter(form_data: Dict[str, Any]) -> str:
    """生成《律师函》文本。"""
    return f"""律 师 函

致：{_get_value(form_data, "recipient")}

本律师受 {_get_value(form_data, "client")} 委托，
就 {_get_value(form_data, "matter")} 事宜，郑重函告如下：

一、事实情况
{_get_value(form_data, "facts")}

二、法律分析
{_get_value(form_data, "legal_analysis")}

三、本律师要求
请贵方于收到本函之日起 {_get_value(form_data, "deadline_days", "7")} 日内，
{_get_value(form_data, "demand")}。
逾期本律师将代表委托人采取包括但不限于诉讼、仲裁等法律措施，届时产生的一切
法律后果由贵方承担。

特此函告！

{_get_value(form_data, "law_firm")}
经办律师：{_get_value(form_data, "lawyer")}
{_get_value(form_data, "date")}
"""


def _generate_power_of_attorney(form_data: Dict[str, Any]) -> str:
    """生成《授权委托书》文本。"""
    return f"""授 权 委 托 书

委托人：{_get_value(form_data, "principal")}
身份证号：{_get_value(form_data, "principal_id_card")}
联系电话：{_get_value(form_data, "principal_phone")}

受托人：{_get_value(form_data, "agent")}
工作单位：{_get_value(form_data, "agent_org")}
联系电话：{_get_value(form_data, "agent_phone")}

现委托上述受托人在我与 {_get_value(form_data, "opponent")}
{_get_value(form_data, "case_reason")} 一案中，作为我的诉讼代理人。

代理权限为：{_get_value(form_data, "scope", "一般代理")}。

本委托书自委托人签字之日起生效，至本案委托事项终结之日止。

委托人（签名）：{_get_value(form_data, "principal")}
{_get_value(form_data, "date")}
"""


# 文书类型 -> 本地模板生成函数 的映射表（新增文书类型时只需在此注册）
_GENERATORS = {
    DOC_TYPE_LAWSUI: _generate_lawsuit,
    DOC_TYPE_DEFENSE: _generate_defense,
    DOC_TYPE_LETTER: _generate_lawyer_letter,
    DOC_TYPE_POWER: _generate_power_of_attorney,
}


def _generate_document_local(doc_type: str, form_data: Dict[str, Any]) -> str:
    """
    本地模板兜底生成（FastGPT 未配置时使用）。

    :param doc_type: 文书类型
    :param form_data: 用户填写的表单数据
    :return: 拼接生成的完整文书文本
    """
    generator = _GENERATORS.get(doc_type)
    if generator is None:
        raise BizException(code=400, message=f"不支持的文书类型：{doc_type}")
    return generator(form_data).strip()


async def generate_document(doc_type: str, form_data: Dict[str, Any]) -> str:
    """
    生成法律文书正文。

    优先调用 FastGPT「文书生成」应用；若未配置或调用失败，降级到本地模板。

    :param doc_type: 文书类型（起诉状/答辩状/律师函/授权委托书）
    :param form_data: 用户填写的表单数据
    :return: 完整文书文本
    :raises BizException: 不支持的文书类型时抛出 400 业务异常
    """
    # 校验文书类型（FastGPT 与本地模板共用同一套类型）
    if doc_type not in _GENERATORS:
        raise BizException(code=400, message=f"不支持的文书类型：{doc_type}")

    # 1) 优先调用 FastGPT
    ai_result = await generate_document_via_fastgpt(doc_type, form_data)
    if ai_result:
        return ai_result.strip()

    # 2) 降级到本地模板
    return _generate_document_local(doc_type, form_data)
