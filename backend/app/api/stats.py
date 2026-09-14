"""
stats.py —— 使用统计接口

路由前缀：/api/v1/stats
接口清单：
- GET /summary  获取当前用户的使用统计（对话/消息/文书/合同数量 + 近7天活跃趋势）
"""

import datetime
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models import Contract, Conversation, DocumentRecord, Message, User
from app.schemas.common import success_response
from app.schemas.user import UserStatsOut

# 全部接口需要登录
router = APIRouter(
    prefix="/stats",
    tags=["使用统计模块"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary", summary="获取当前用户的使用统计")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户使用统计：
    1. 对话总数、消息总数、文书总数、合同总数、已审查合同数；
    2. 近 7 天每日活跃次数（综合对话/消息/文书/合同创建事件，按日期聚合）。

    用于个人中心展示调用趋势图与汇总数字。
    """
    uid = current_user.id

    # -------- 1. 各资源总数（均为标量聚合查询，单条 SQL 各自完成） --------
    conversation_count = db.scalar(
        select(func.count(Conversation.id)).where(Conversation.user_id == uid)
    ) or 0

    # 消息总数：需要 join conversations 过滤本用户对话
    message_count = db.scalar(
        select(func.count(Message.id))
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == uid)
    ) or 0

    document_count = db.scalar(
        select(func.count(DocumentRecord.id)).where(DocumentRecord.user_id == uid)
    ) or 0

    contract_count = db.scalar(
        select(func.count(Contract.id)).where(Contract.user_id == uid)
    ) or 0

    # 已完成审查：review_result 不为空
    reviewed_contract_count = db.scalar(
        select(func.count(Contract.id)).where(
            Contract.user_id == uid, Contract.review_result.isnot(None)
        )
    ) or 0

    # -------- 2. 近 7 天活跃数据 --------
    # 取近 7 天（含今天）每日的活跃事件计数。活跃事件 = 用户产生了新的对话/消息/文书/合同记录。
    # 由于各表 created_at 字段一致，使用 union all 汇总后按日期聚合。
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=6)  # 含今天共 7 天

    # 各表查询 (日期, 次数) 二元组
    def _daily_counts(model, date_col, where_clause):
        return db.execute(
            select(
                func.date(date_col).label("d"),
                func.count(model.id).label("c"),
            ).where(where_clause, func.date(date_col) >= seven_days_ago).group_by("d")
        ).all()

    # 对话创建
    conv_rows = _daily_counts(
        Conversation, Conversation.created_at, Conversation.user_id == uid
    )
    # 消息创建（需要过滤归属本用户对话）
    msg_rows = db.execute(
        select(
            func.date(Message.created_at).label("d"),
            func.count(Message.id).label("c"),
        )
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == uid, func.date(Message.created_at) >= seven_days_ago)
        .group_by("d")
    ).all()
    # 文书创建
    doc_rows = _daily_counts(
        DocumentRecord, DocumentRecord.created_at, DocumentRecord.user_id == uid
    )
    # 合同上传
    contract_rows = _daily_counts(
        Contract, Contract.created_at, Contract.user_id == uid
    )

    # 把所有事件按日期汇总
    daily_map = defaultdict(int)
    for d, c in conv_rows:
        daily_map[str(d)] += c
    for d, c in msg_rows:
        daily_map[str(d)] += c
    for d, c in doc_rows:
        daily_map[str(d)] += c
    for d, c in contract_rows:
        daily_map[str(d)] += c

    # 补全 7 天空档（保证前端拿到固定 7 个数据点，便于画图）
    recent_activity = []
    for i in range(7):
        d = seven_days_ago + datetime.timedelta(days=i)
        ds = d.isoformat()  # YYYY-MM-DD
        # 周几：0=周一 ... 6=周日；前端可展示"周X"
        recent_activity.append({"date": ds, "weekday": d.weekday(), "count": daily_map.get(ds, 0)})

    data = UserStatsOut(
        conversation_count=conversation_count,
        message_count=message_count,
        document_count=document_count,
        contract_count=contract_count,
        reviewed_contract_count=reviewed_contract_count,
        recent_activity=recent_activity,
    )
    return success_response(data=data.model_dump(mode="json"))
