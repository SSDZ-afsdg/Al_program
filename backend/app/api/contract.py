"""
contract.py —— 合同审查接口

路由前缀：/api/v1/contracts
接口清单：
- POST /upload           上传合同文件（.docx / .pdf），解析并保存原文
- POST /review/{id}      对已上传的合同执行 AI 风险审查
- GET  /list             获取当前用户的审查历史列表
- GET  /{id}             获取合同记录详情（含原文全文，供前端风险定位高亮）
- GET  /{id}/export-pdf  将审查报告导出为 PDF 文件下载
"""

import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_user
from app.core.exceptions import BizException, ForbiddenException, NotFoundException
from app.database import get_db
from app.models import Contract, User
from app.schemas.common import success_response
from app.schemas.contract import ContractUploadOut
from app.services.contract_service import review_contract
from app.utils.file_handler import extract_text
from app.utils.pdf_report import build_review_report_pdf

# 全部接口需要登录
router = APIRouter(
    prefix="/contracts",
    tags=["合同审查模块"],
    dependencies=[Depends(get_current_user)],
)


def _get_owned_contract(db: Session, contract_id: int, user: User) -> Contract:
    """
    查询指定合同记录并校验归属权（内部复用的辅助函数）。

    :raises NotFoundException: 记录不存在
    :raises ForbiddenException: 记录不属于当前用户
    """
    contract = db.get(Contract, contract_id)
    if contract is None:
        raise NotFoundException("合同记录不存在")
    if contract.user_id != user.id:
        raise ForbiddenException("无权操作该合同记录")
    return contract


@router.post("/upload", summary="上传合同文件")
async def upload_contract(
    file: UploadFile = File(..., description="合同文件，仅支持 .docx / .pdf"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传合同文件接口：
    1. 校验扩展名与文件大小；
    2. 以 UUID 重命名保存到上传目录，避免文件名冲突与路径穿越；
    3. 调用文件解析工具提取合同纯文本；
    4. 将文件信息与原文落库，返回记录 ID 与文本预览（供下一步审查使用）。
    """
    # -------- 1. 校验扩展名 --------
    original_name = file.filename or ""
    # 取扩展名并转小写
    suffix = Path(original_name).suffix.lower()  # 形如 ".docx"
    allowed_exts = {f".{ext.strip().lower()}" for ext in settings.ALLOWED_EXTENSIONS.split(",")}
    if suffix not in allowed_exts:
        raise BizException(
            code=400,
            message=f"不支持的文件类型：{suffix or '未知'}，仅支持 .docx / .pdf",
        )

    # -------- 2. 读取文件内容并校验大小 --------
    content_bytes = await file.read()
    if len(content_bytes) == 0:
        raise BizException(code=400, message="上传文件内容为空")
    if len(content_bytes) > settings.MAX_FILE_SIZE:
        # 将字节数换算为 MB 提示
        max_mb = settings.MAX_FILE_SIZE / 1024 / 1024
        raise BizException(code=400, message=f"文件大小超出限制，最大允许 {max_mb:.0f}MB")

    # -------- 3. 确保上传目录存在并保存文件 --------
    upload_dir = settings.upload_path
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 使用 UUID 生成新文件名，防止中文文件名、重名与路径穿越问题
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    saved_path = upload_dir / stored_name
    # 以二进制方式写入磁盘
    saved_path.write_bytes(content_bytes)

    # -------- 4. 提取合同文本 --------
    try:
        original_text = extract_text(saved_path)
    except BizException:
        # 解析失败时清理已保存的文件，避免产生垃圾文件
        saved_path.unlink(missing_ok=True)
        raise

    # -------- 5. 落库 --------
    contract = Contract(
        user_id=current_user.id,
        file_name=original_name,
        # 数据库保存相对路径（相对后端根目录），迁移部署时更灵活
        file_path=str(Path(settings.UPLOAD_DIR) / stored_name),
        original_text=original_text,
        review_result=None,  # 刚上传尚未审查
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    # 组装响应数据
    data = ContractUploadOut(
        id=contract.id,
        file_name=contract.file_name,
        text_length=len(original_text),
        text_preview=original_text[:200],
    )
    return success_response(data=data.model_dump(mode="json"), message="文件上传并解析成功")


@router.post("/review/{contract_id}", summary="执行合同风险审查")
async def review(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    对已上传的合同执行风险审查：
    1. 校验记录存在且归属当前用户；
    2. 调用审查服务（优先 FastGPT 智能审查，未配置则降级本地规则）；
    3. 将审查结果以 JSON 写回记录并返回。
    """
    contract = _get_owned_contract(db, contract_id, current_user)

    # 调用业务服务进行审查（FastGPT 优先，本地规则兜底）
    result = await review_contract(contract.original_text)

    # 将审查结果回写到记录
    contract.review_result = result
    db.add(contract)
    db.commit()
    db.refresh(contract)

    return success_response(
        data={
            "id": contract.id,
            "file_name": contract.file_name,
            "review_result": contract.review_result,
        },
        message="合同审查完成",
    )


@router.get("/list", summary="获取合同审查历史列表")
def list_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的合同上传/审查历史，按上传时间倒序。"""
    records = db.scalars(
        select(Contract)
        .where(Contract.user_id == current_user.id)
        .order_by(desc(Contract.created_at), desc(Contract.id))
    ).all()

    # 组装列表数据：审查结果为空表示尚未审查
    data = []
    for record in records:
        data.append(
            {
                "id": record.id,
                "file_name": record.file_name,
                "reviewed": record.review_result is not None,
                "review_result": record.review_result,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
        )

    return success_response(data=data)


@router.get("/{contract_id}", summary="获取合同记录详情")
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取合同记录详情（含原文全文与审查结果）。

    用途：前端展示"合同原文 + 风险条款定位高亮"视图时，
    需要完整原文文本（上传接口只返回 200 字预览，不满足定位需求）。
    """
    contract = _get_owned_contract(db, contract_id, current_user)

    return success_response(
        data={
            "id": contract.id,
            "file_name": contract.file_name,
            "original_text": contract.original_text,
            "review_result": contract.review_result,
            "created_at": contract.created_at.isoformat() if contract.created_at else None,
        }
    )


@router.get("/{contract_id}/export-pdf", summary="导出审查报告 PDF")
def export_review_pdf(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    将合同审查结果导出为 PDF 报告：
    1. 校验记录归属与审查状态（未审查的记录无法导出报告）；
    2. 调用 reportlab 在内存中生成排版美观的审查报告；
    3. 以文件流返回，浏览器触发下载。
    """
    contract = _get_owned_contract(db, contract_id, current_user)

    # 尚未审查的记录没有报告内容可导出
    if not contract.review_result:
        raise BizException(code=400, message="该合同尚未完成审查，无法导出报告")

    # 生成 PDF 二进制内容（内存中完成，不落盘）
    try:
        pdf_bytes = build_review_report_pdf(
            review_result=contract.review_result,
            file_name=contract.file_name,
            reviewed_at=contract.created_at or datetime.now(),
        )
    except RuntimeError as e:
        # 中文字体缺失等环境问题，返回可读的业务错误提示
        raise BizException(code=500, message=str(e))

    # 下载文件名：审查报告_{原文件名去扩展名}.pdf
    stem = Path(contract.file_name).stem or f"contract_{contract.id}"
    download_name = f"审查报告_{stem}.pdf"
    # 中文文件名按 RFC 5987 用 filename* 编码，避免浏览器乱码
    quoted_name = quote(download_name)

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quoted_name}",
        },
    )
