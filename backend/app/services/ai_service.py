"""
ai_service.py —— AI 调用封装服务（对接 FastGPT，支持三套应用）

三个功能模块各自使用独立的 FastGPT 应用：
- AI法律咨询：使用 FASTGPT_CHAT_* 配置
- 文书生成：使用 FASTGPT_DOC_* 配置
- 合同审查：使用 FASTGPT_CONTRACT_* 配置

FastGPT 接口要点：
- 请求地址：{BASE_URL}/api/v1/chat/completions
- 鉴权：Authorization: Bearer {API_KEY}
- 请求体：appId、chatId、stream=false、messages=[{role, content}]
- 响应：choices[0].message.content 即为 AI 回复文本
"""

import json
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.core.exceptions import BizException
from app.models import Message


# 业务类型常量：对应三个功能模块
BUSINESS_CHAT = "chat"        # AI法律咨询
BUSINESS_DOC = "doc"          # 文书生成
BUSINESS_CONTRACT = "contract"  # 合同审查


def _get_fastgpt_config(business_type: str) -> Dict[str, str]:
    """
    根据业务类型获取对应的 FastGPT 配置。

    :return: {"base_url": ..., "api_key": ..., "app_id": ...}
    :raises BizException: 未配置或仍为占位符时抛出 501（功能未启用）
    """
    # 根据业务类型映射到对应的配置字段前缀
    prefix_map = {
        BUSINESS_CHAT: "FASTGPT_CHAT",
        BUSINESS_DOC: "FASTGPT_DOC",
        BUSINESS_CONTRACT: "FASTGPT_CONTRACT",
    }
    prefix = prefix_map.get(business_type)
    if prefix is None:
        raise BizException(code=400, message=f"未知的业务类型：{business_type}")

    # 从 settings 中动态读取三项配置
    base_url = getattr(settings, f"{prefix}_BASE_URL").strip()
    api_key = getattr(settings, f"{prefix}_API_KEY").strip()
    app_id = getattr(settings, f"{prefix}_APP_ID").strip()

    # 未配置或仍是占位符（含 "your-"）时，提示用户配置
    if not api_key or not app_id or "your-" in api_key or "your-" in app_id:
        raise BizException(
            code=501,
            message=(
                f"FastGPT「{business_type}」应用尚未配置，请在 backend/.env 中填写 "
                f"{prefix}_BASE_URL、{prefix}_API_KEY、{prefix}_APP_ID 后重启后端服务。"
            ),
        )

    return {"base_url": base_url, "api_key": api_key, "app_id": app_id}


def _is_configured(business_type: str) -> bool:
    """判断指定业务类型的 FastGPT 是否已配置（不抛异常）。"""
    try:
        _get_fastgpt_config(business_type)
        return True
    except BizException:
        return False


# FastGPT 业务错误码 -> 中文提示 的映射表
_FASTGPT_ERROR_MAP = {
    514: "API Key 鉴权失败，请检查 API Key 是否正确、是否为应用特定 Key，或是否已过期",
    500: "应用不存在或无权限访问，请检查 AppId 是否正确",
    400: "请求参数错误",
    401: "未授权",
    403: "无权限",
    404: "资源不存在",
    429: "请求过于频繁，已触发限流，请稍后重试",
}


def _fastgpt_biz_error(business_type: str, http_status: int, result: Dict) -> BizException:
    """
    将 FastGPT 返回的业务错误转换为友好的 BizException。

    :param business_type: 业务类型
    :param http_status: HTTP 状态码
    :param result: FastGPT 返回的 JSON 字典
    :return: BizException 异常
    """
    code = result.get("code", http_status)
    status_text = result.get("statusText", "")
    raw_msg = result.get("message", "")

    # 优先用错误码映射，其次用 statusText，最后用原始 message
    friendly = _FASTGPT_ERROR_MAP.get(code)
    if not friendly:
        friendly = status_text or raw_msg or f"HTTP {http_status}"

    return BizException(
        code=502,
        message=f"FastGPT「{business_type}」调用失败（错误码 {code}）：{friendly}",
    )


async def _call_fastgpt(
    business_type: str,
    messages: List[Dict[str, str]],
    chat_id: Optional[str] = None,
) -> str:
    """
    通用 FastGPT 对话调用。

    :param business_type: 业务类型，决定使用哪套 FastGPT 应用配置
    :param messages: 消息列表，格式 [{role: "user"/"assistant", content: "..."}]
    :param chat_id: 可选，FastGPT 会话 ID（非空时由 FastGPT 维护上下文）
    :return: AI 回复的文本内容
    :raises BizException: 配置缺失、网络错误、响应解析失败时抛出
    """
    config = _get_fastgpt_config(business_type)

    # 拼接请求地址：兼容 base_url 是否带 /api 两种写法
    # 云服务示例：base_url=https://cloud.fastgpt.cn -> /api/v1/chat/completions
    # 自建示例：base_url=http://localhost:3000/api -> /v1/chat/completions
    base_url = config["base_url"].rstrip("/")
    if base_url.endswith("/api"):
        url = f"{base_url}/v1/chat/completions"
    else:
        url = f"{base_url}/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "appId": config["app_id"],
        "stream": False,
        "detail": False,
        "messages": messages,
    }
    # 仅在传入 chat_id 时附加（法律咨询需要上下文，文书/合同审查单轮不需要）
    if chat_id:
        payload["chatId"] = chat_id

    # 发起异步 HTTP 请求
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            # FastGPT 业务错误会返回非 2xx 状态码且 body 中带 code/message
            result = resp.json()
            if resp.status_code >= 400 or result.get("code", 0) != 0:
                raise _fastgpt_biz_error(business_type, resp.status_code, result)
            content = (result.get("choices") or [{}])[0].get("message", {}).get("content", "")
            if not content:
                raise BizException(code=502, message=f"FastGPT「{business_type}」返回的回复内容为空")
            return content
    except httpx.RequestError as e:
        raise BizException(code=502, message=f"无法连接 FastGPT「{business_type}」服务：{e}")
    except json.JSONDecodeError:
        raise BizException(code=502, message=f"FastGPT「{business_type}」响应不是合法 JSON")


async def _call_fastgpt_stream(
    business_type: str,
    messages: List[Dict[str, str]],
    chat_id: Optional[str] = None,
):
    """
    通用 FastGPT 流式对话调用（异步生成器，逐块 yield 文本片段）。

    FastGPT stream=true 时返回 SSE 格式：
        data: {"choices":[{"delta":{"content":"片段文本"}}]}
        ...
        data: [DONE]

    :yield: 每收到一段文本就 yield 该字符串片段
    :raises BizException: 配置缺失、网络错误时抛出
    """
    config = _get_fastgpt_config(business_type)

    base_url = config["base_url"].rstrip("/")
    if base_url.endswith("/api"):
        url = f"{base_url}/v1/chat/completions"
    else:
        url = f"{base_url}/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "appId": config["app_id"],
        "stream": True,       # 开启流式
        "detail": False,
        "messages": messages,
    }
    if chat_id:
        payload["chatId"] = chat_id

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as resp:
                # 业务错误：非流式地返回 JSON 错误体
                if resp.status_code >= 400:
                    body = await resp.aread()
                    try:
                        result = json.loads(body)
                    except json.JSONDecodeError:
                        result = {"message": body.decode("utf-8", errors="ignore")[:300]}
                    raise _fastgpt_biz_error(business_type, resp.status_code, result)

                # 逐行解析 SSE 数据流
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue
                    # 提取 delta.content 文本片段
                    delta = (chunk.get("choices") or [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield content
    except httpx.RequestError as e:
        raise BizException(code=502, message=f"无法连接 FastGPT「{business_type}」服务：{e}")


def build_fastgpt_chat_id(conversation_id: int) -> str:
    """
    根据本系统对话 ID 生成 FastGPT 的 chatId（仅法律咨询使用）。

    FastGPT 要求 chatId 唯一且长度 < 250，使用前缀 + 自增 ID 可保证唯一性，
    同时便于排查时与本系统对话记录对应。
    """
    return f"fabao_chat_{conversation_id}"


# ============================================================================
# 以下为三个业务模块对外暴露的 AI 调用函数
# ============================================================================


async def get_ai_reply(
    history: List[Message],
    user_content: str,
    conversation_id: int,
) -> str:
    """
    AI法律咨询：调用 FastGPT 对话接口获取法律回复。

    使用 chatId 让 FastGPT 维护多轮上下文，仅传本轮用户问题。
    """
    messages = [{"role": "user", "content": user_content}]
    return await _call_fastgpt(
        business_type=BUSINESS_CHAT,
        messages=messages,
        chat_id=build_fastgpt_chat_id(conversation_id),
    )


async def get_ai_reply_stream(
    user_content: str,
    conversation_id: int,
):
    """
    AI法律咨询（流式）：逐块 yield AI 回复文本片段。

    使用 chatId 让 FastGPT 维护多轮上下文，仅传本轮用户问题。
    用于 SSE 流式输出场景，前端可实时显示打字效果。
    """
    messages = [{"role": "user", "content": user_content}]
    async for chunk in _call_fastgpt_stream(
        business_type=BUSINESS_CHAT,
        messages=messages,
        chat_id=build_fastgpt_chat_id(conversation_id),
    ):
        yield chunk


async def generate_document_via_fastgpt(
    doc_type: str,
    form_data: Dict[str, Any],
) -> str:
    """
    文书生成：调用 FastGPT 生成法律文书。

    将文书类型与表单数据组装成结构化提示词，要求 FastGPT 返回完整文书正文。
    若 FastGPT 未配置，则返回 None 由调用方降级到本地模板。
    """
    if not _is_configured(BUSINESS_DOC):
        return None

    # 将表单数据格式化为易读的键值对文本
    fields_text = "\n".join(f"- {k}：{v}" for k, v in form_data.items() if v)

    prompt = (
        f"请根据以下信息生成一份完整、规范的「{doc_type}」。\n"
        f"要求：\n"
        f"1. 使用标准法律文书格式，包含必要的首部、正文、尾部；\n"
        f"2. 内容专业、严谨，符合中国大陆法律文书规范；\n"
        f"3. 仅输出文书正文，不要附加解释说明。\n\n"
        f"【表单信息】\n{fields_text}\n"
    )

    messages = [{"role": "user", "content": prompt}]
    return await _call_fastgpt(business_type=BUSINESS_DOC, messages=messages)


async def review_contract_via_fastgpt(original_text: str) -> Optional[Dict]:
    """
    合同审查：调用 FastGPT 对合同进行风险审查。

    要求 FastGPT 返回 JSON 结构的风险列表，本函数负责解析并标准化为
    {risk_level, summary, risks: [{level, clause, analysis, suggestion}]}。
    若 FastGPT 未配置或解析失败，则返回 None 由调用方降级。
    """
    if not _is_configured(BUSINESS_CONTRACT):
        return None

    prompt = (
        "请作为专业法律顾问，对以下合同文本进行风险审查。\n"
        "请以严格的 JSON 格式返回结果，不要包含任何其他文字或 markdown 标记。\n"
        "JSON 结构如下：\n"
        "{\n"
        '  "risk_level": "高" 或 "中" 或 "低",\n'
        '  "summary": "总体审查意见（不超过 100 字）",\n'
        '  "risks": [\n'
        "    {\n"
        '      "level": "高" 或 "中" 或 "低",\n'
        '      "clause": "合同中对应的原文条款引用",\n'
        '      "analysis": "风险分析",\n'
        '      "suggestion": "修改建议"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "要求：\n"
        "1. 至少识别 3 条风险，覆盖高、中、低三个等级；\n"
        "2. clause 字段必须引用合同原文中的具体条款；\n"
        "3. 分析和建议要专业、具体、可操作。\n\n"
        f"【合同原文】\n{original_text}\n"
    )

    messages = [{"role": "user", "content": prompt}]
    try:
        raw = await _call_fastgpt(business_type=BUSINESS_CONTRACT, messages=messages)
    except BizException:
        # FastGPT 调用失败，返回 None 让调用方降级
        return None

    # 解析 JSON：FastGPT 可能在 JSON 外包裹 ```json 代码块，需去除
    text = raw.strip()
    # 去除可能的 markdown 代码块标记
    if text.startswith("```"):
        # 按行分割，去掉首尾的 ``` 行
        lines = text.split("\n")
        # 移除首行 ```json 或 ```
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        # 移除末行 ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        # JSON 解析失败，降级
        return None

    # 标准化字段，确保返回结构符合预期
    risk_level = result.get("risk_level", "中")
    summary = result.get("summary", "")
    risks = result.get("risks", [])

    # 校验 risks 列表中每条风险的字段完整性
    normalized_risks = []
    for r in risks:
        if not isinstance(r, dict):
            continue
        normalized_risks.append({
            "level": r.get("level", "中"),
            "clause": r.get("clause", ""),
            "analysis": r.get("analysis", ""),
            "suggestion": r.get("suggestion", ""),
        })

    if not normalized_risks:
        return None

    return {
        "risk_level": risk_level,
        "summary": summary,
        "risks": normalized_risks,
    }
