"""
chat.py —— AI 法律咨询接口

路由前缀：/api/v1/chat
接口清单：
- GET    /conversations               获取当前用户的对话列表
- POST   /conversations               新建对话
- DELETE /conversations/{id}          删除指定对话
- GET    /conversations/{id}/messages 获取指定对话的消息列表
- POST   /conversations/{id}/messages 发送消息并获取 AI 回复

注意：除新建/列表外，所有操作都会校验对话归属权，防止越权访问他人数据。
"""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.exceptions import BizException, ForbiddenException, NotFoundException
from app.database import get_db
from app.models import Conversation, Message, User
from app.schemas.chat import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
)
from app.schemas.common import success_response
from app.services.ai_service import get_ai_reply, get_ai_reply_stream

# 所有对话接口都需要登录，直接在路由级别声明鉴权依赖
router = APIRouter(
    prefix="/chat",
    tags=["AI法律咨询模块"],
    dependencies=[Depends(get_current_user)],
)


def _get_owned_conversation(db: Session, conversation_id: int, user: User) -> Conversation:
    """
    查询指定对话并校验归属权（内部复用的辅助函数）。

    :raises NotFoundException: 对话不存在
    :raises ForbiddenException: 对话不属于当前用户
    """
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise NotFoundException("对话不存在")
    if conversation.user_id != user.id:
        # 不暴露他人资源是否存在，直接返回 403 也可；这里语义为"无权操作"
        raise ForbiddenException("无权操作该对话")
    return conversation


@router.get("/conversations", summary="获取对话列表")
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的全部对话，按更新时间倒序排列（最近对话在前）。"""
    conversations = db.scalars(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(desc(Conversation.updated_at), desc(Conversation.id))
    ).all()

    # 批量序列化为输出模型
    data = [ConversationOut.model_validate(item).model_dump(mode="json") for item in conversations]
    return success_response(data=data)


@router.post("/conversations", summary="新建对话")
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """为当前用户新建一个空对话，返回对话信息（含对话 id）。"""
    # 标题未传时使用默认标题
    conversation = Conversation(
        user_id=current_user.id,
        title=payload.title or "新的法律咨询",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return success_response(
        data=ConversationOut.model_validate(conversation).model_dump(mode="json"),
        message="对话创建成功",
    )


@router.delete("/conversations/{conversation_id}", summary="删除对话")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除指定对话（消息随外键级联一并删除）。"""
    conversation = _get_owned_conversation(db, conversation_id, current_user)

    db.delete(conversation)
    db.commit()
    return success_response(message="对话删除成功")


@router.get("/conversations/{conversation_id}/messages", summary="获取对话消息列表")
def list_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定对话下的全部消息，按时间正序（方便前端按对话流渲染）。"""
    conversation = _get_owned_conversation(db, conversation_id, current_user)

    # 显式按创建时间正序查询消息
    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at, Message.id)
    ).all()

    data = [MessageOut.model_validate(msg).model_dump(mode="json") for msg in messages]
    return success_response(data=data)


@router.post("/conversations/{conversation_id}/messages", summary="发送消息并获取AI回复")
async def send_message(
    conversation_id: int,
    payload: MessageCreate,  # 请求体：{"content": "用户问题"}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    发送一条用户消息并获取 AI 回复：
    1. 校验对话归属；
    2. 保存用户消息；
    3. 调用 AI 服务生成回复（当前为模拟实现）；
    4. 保存 AI 回复消息并返回两条消息。
    """
    conversation = _get_owned_conversation(db, conversation_id, current_user)

    # 1) 保存用户消息
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.content,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # 2) 取对话历史（供大模型理解上下文，当前模拟服务仅用于计数）
    history = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at, Message.id)
    ).all()

    # 3) 调用 AI 服务（异步，对接 FastGPT 真实接口）
    #    传入 conversation.id 用于生成 FastGPT 的 chatId，由 FastGPT 维护对话上下文
    ai_text = await get_ai_reply(history, payload.content, conversation.id)

    # 4) 保存 AI 助手回复
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_text,
    )
    db.add(assistant_message)

    # 若是对话中的第一条用户消息，则用问题前 20 个字更新对话标题
    user_msg_count = sum(1 for msg in history if msg.role == "user")
    if user_msg_count == 1:
        conversation.title = payload.content[:20] + ("..." if len(payload.content) > 20 else "")
        db.add(conversation)

    db.commit()
    db.refresh(assistant_message)

    # 返回用户消息与 AI 回复，前端可直接追加到聊天窗口
    data = {
        "user_message": MessageOut.model_validate(user_message).model_dump(mode="json"),
        "assistant_message": MessageOut.model_validate(assistant_message).model_dump(mode="json"),
    }
    return success_response(data=data, message="回复成功")


@router.post("/conversations/{conversation_id}/messages/stream", summary="发送消息并流式获取AI回复")
async def send_message_stream(
    conversation_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    流式发送消息接口（SSE）：
    1. 校验对话归属，保存用户消息；
    2. 以 SSE 格式逐块推送 AI 回复文本（data: {"content": "..."}）；
    3. 流结束后将完整回复落库，并推送 [DONE] 事件。

    前端使用 fetch + ReadableStream 接收，实时拼接内容实现打字效果。
    """
    conversation = _get_owned_conversation(db, conversation_id, current_user)

    # 1) 保存用户消息
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.content,
    )
    db.add(user_message)
    db.commit()

    # 2) 取历史（用于判断是否为首条消息以更新标题）
    history = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at, Message.id)
    ).all()
    is_first_user_msg = sum(1 for m in history if m.role == "user") == 1

    async def event_generator() -> AsyncGenerator[str, None]:
        full_text = ""
        try:
            # 流式接收 FastGPT 回复，逐块推送给前端
            async for chunk in get_ai_reply_stream(payload.content, conversation.id):
                full_text += chunk
                # SSE 格式：data: {json}\n\n
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

            # 3) 流结束后保存 AI 回复到数据库
            assistant_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_text,
            )
            db.add(assistant_message)
            if is_first_user_msg:
                conversation.title = payload.content[:20] + ("..." if len(payload.content) > 20 else "")
                db.add(conversation)
            db.commit()

            # 推送结束事件（携带 assistant_message id 供前端关联）
            db.refresh(assistant_message)
            yield f"data: {json.dumps({'done': True, 'message_id': assistant_message.id}, ensure_ascii=False)}\n\n"
        except BizException as e:
            # 业务错误：推送错误事件后结束
            yield f"data: {json.dumps({'error': e.message, 'code': e.code}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'AI 服务异常：{e}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲，保证流式实时推送
        },
    )
