"""
document.py —— 文书生成接口

路由前缀：/api/v1/documents
接口清单：
- POST /generate  提交表单数据并生成文书
- GET  /list      获取当前用户的文书历史列表
- GET  /{id}      获取某条文书记录详情

路由顺序注意：/list 必须定义在 /{id} 之前，否则 "list" 会被当作 id 匹配。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.exceptions import ForbiddenException, NotFoundException
from app.database import get_db
from app.models import DocumentRecord, User
from app.schemas.common import success_response
from app.schemas.document import (
    DocumentGenerateRequest,
    DocumentListItem,
    DocumentOut,
)
from app.services.document_service import generate_document

# 全部接口需要登录
router = APIRouter(
    prefix="/documents",
    tags=["文书生成模块"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/generate", summary="生成法律文书")
async def generate(
    payload: DocumentGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    文书生成接口：
    1. 接收文书类型与表单数据（schema 层已校验类型合法性）；
    2. 调用服务层优先走 FastGPT 生成文书正文，未配置则降级本地模板；
    3. 将表单数据与生成结果一并落库，返回完整记录。
    """
    # 调用业务层生成文书文本（FastGPT 优先，本地模板兜底）
    content = await generate_document(payload.doc_type, payload.form_data)

    # 创建生成记录
    record = DocumentRecord(
        user_id=current_user.id,
        doc_type=payload.doc_type,
        form_data=payload.form_data,
        generated_content=content,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success_response(
        data=DocumentOut.model_validate(record).model_dump(mode="json"),
        message="文书生成成功",
    )


@router.get("/list", summary="获取文书历史列表")
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的文书生成历史（不含完整正文，仅返回前 100 字预览）。"""
    records = db.scalars(
        select(DocumentRecord)
        .where(DocumentRecord.user_id == current_user.id)
        .order_by(desc(DocumentRecord.created_at), desc(DocumentRecord.id))
    ).all()

    # 组装列表项数据：id / 类型 / 正文预览 / 时间
    data = []
    for record in records:
        item = DocumentListItem(
            id=record.id,
            doc_type=record.doc_type,
            content_preview=record.generated_content[:100],
            created_at=record.created_at,
        )
        data.append(item.model_dump(mode="json"))

    return success_response(data=data)


@router.get("/{record_id}", summary="获取文书记录详情")
def get_document(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据 ID 获取单条文书记录的完整内容（含正文全文）。"""
    record = db.get(DocumentRecord, record_id)
    if record is None:
        raise NotFoundException("文书记录不存在")
    # 越权校验：只能查看自己的记录
    if record.user_id != current_user.id:
        raise ForbiddenException("无权查看该文书记录")

    return success_response(
        data=DocumentOut.model_validate(record).model_dump(mode="json")
    )
