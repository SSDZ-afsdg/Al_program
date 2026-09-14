"""
pdf_report.py —— 合同审查报告 PDF 生成工具

使用 reportlab 将合同审查结果渲染为排版美观的 PDF 报告：
- 报告标题、审查对象、审查时间
- 总体风险等级徽章 + 高/中/低风险统计
- 逐条风险详情（等级 / 原文引用 / 风险分析 / 修改建议）

中文字体处理：
reportlab 内置字体不含中文，必须注册系统中文字体后才能正常显示。
按 Windows / Linux(Docker) 常见字体路径依次探测，找到即注册使用；
全部缺失时抛出带安装指引的异常，便于部署时快速定位。
"""

import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# 报告主色（与前端主题一致：深蓝 + 金色点缀）
PRIMARY_DARK = colors.HexColor("#1a3a5c")
GOLD = colors.HexColor("#c9a96e")
TEXT_GREY = colors.HexColor("#5a6a7a")

# 三档风险的展示色（与前端 levelMeta 保持一致）
RISK_COLORS = {
    "高": colors.HexColor("#c0392b"),
    "中": colors.HexColor("#e67e22"),
    "低": colors.HexColor("#27ae60"),
}

# 中文字体候选路径（按顺序探测，命中即用）
_FONT_CANDIDATES = [
    # Windows：微软雅黑 / 黑体 / 宋体
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
    # Linux（Docker 中 apt 安装 fonts-noto-cjk 后的路径）
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
]

# 注册后的字体名称（全局注册一次，重复调用直接复用）
_FONT_NAME = "FabaoCJK"


def _ensure_chinese_font() -> str:
    """
    确保中文字体已注册（幂等：已注册则直接返回字体名）。

    :return: 可用于 Paragraph/Style 的字体名称
    :raises RuntimeError: 系统中找不到任何可用中文字体
    """
    if _FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return _FONT_NAME

    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(_FONT_NAME, path))
                return _FONT_NAME
            except Exception:
                # 个别字体文件注册失败（损坏/格式不支持），继续尝试下一个
                continue

    raise RuntimeError(
        "未找到可用的中文字体，无法生成 PDF 报告。"
        "Windows 请确认系统字体完好；"
        "Linux/Docker 请安装 fonts-noto-cjk（apt install -y fonts-noto-cjk）。"
    )


# ---------------------------------------------------------------------------
# 段落样式（全部基于注册的中文字体）
# ---------------------------------------------------------------------------

def _build_styles():
    """构建报告所需的全套段落样式（字体注册后调用）。"""
    font = _ensure_chinese_font()
    return {
        # 报告主标题
        "title": ParagraphStyle(
            "title", fontName=font, fontSize=20, leading=28,
            alignment=1, textColor=PRIMARY_DARK, spaceAfter=4,  # 1=居中
        ),
        # 标题下方副信息行
        "subtitle": ParagraphStyle(
            "subtitle", fontName=font, fontSize=10.5, leading=16,
            alignment=1, textColor=TEXT_GREY, spaceAfter=2,
        ),
        # 分区标题
        "section": ParagraphStyle(
            "section", fontName=font, fontSize=14, leading=20,
            textColor=PRIMARY_DARK, spaceBefore=14, spaceAfter=8,
        ),
        # 正文
        "body": ParagraphStyle(
            "body", fontName=font, fontSize=10.5, leading=17,
            textColor=colors.HexColor("#333333"), spaceAfter=4,
        ),
        # 风险卡片内的标签文字
        "label": ParagraphStyle(
            "label", fontName=font, fontSize=10.5, leading=16,
            textColor=TEXT_GREY,
        ),
        # 原文引用（斜体不适用于中文，用深色+浅底衬托）
        "clause": ParagraphStyle(
            "clause", fontName=font, fontSize=10, leading=15,
            textColor=colors.HexColor("#3d4a56"),
        ),
    }


def _clean(text: Any) -> str:
    """清洗文本：空值转空串，并转义 XML 特殊字符（Paragraph 按轻量 XML 解析）。"""
    if text is None:
        return ""
    text = str(text)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _risk_badge(level: str) -> Table:
    """
    生成单个风险等级徽章（带底色的小表格，视觉上等价于前端 el-tag）。

    :param level: 风险等级：高 / 中 / 低
    """
    color = RISK_COLORS.get(level, colors.grey)
    cell = Paragraph(
        f"<font color='white'><b>{_clean(level)}风险</b></font>",
        ParagraphStyle("badge", fontName=_FONT_NAME, fontSize=10, leading=14, alignment=1),
    )
    t = Table([[cell]], colWidths=[2.2 * cm], rowHeights=[0.62 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return t


def _risk_card(idx: int, risk: Dict[str, Any], styles: dict) -> List:
    """
    构建单条风险的展示卡片（多个 flowable 组合，用 KeepTogether 防跨页断开）。

    :param idx: 风险序号（从 1 开始）
    :param risk: 风险条目 {level, clause, analysis, suggestion}
    """
    level = str(risk.get("level", "中"))
    color = RISK_COLORS.get(level, colors.grey)

    # 卡片头部：等级徽章 + 风险序号
    header = Table(
        [[_risk_badge(level),
          Paragraph(f"<b>风险条款 #{idx}</b>", styles["body"]),
          Paragraph(_clean(risk.get("clause_type", "")), styles["label"])]],
        colWidths=[2.4 * cm, 4 * cm, None],
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))

    rows: List = [header]

    # 原文引用块：左侧金色竖线效果用表格左边框模拟
    clause_text = _clean(risk.get("clause", ""))
    if clause_text:
        clause_para = Paragraph(clause_text, styles["clause"])
        clause_tbl = Table([[clause_para]], colWidths=[None])
        clause_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf6ee")),
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, GOLD),  # 左侧金色竖线
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        rows += [Spacer(1, 2), clause_tbl]

    # 风险分析
    analysis = _clean(risk.get("analysis", ""))
    if analysis:
        rows += [Spacer(1, 4), Paragraph(
            f"<font color='#1a3a5c'><b>风险分析：</b></font>{analysis}", styles["body"]
        )]

    # 修改建议
    suggestion = _clean(risk.get("suggestion", ""))
    if suggestion:
        rows += [Paragraph(
            f"<font color='#27ae60'><b>修改建议：</b></font>{suggestion}", styles["body"]
        )]

    rows.append(Spacer(1, 10))
    return [KeepTogether(rows)]


def build_review_report_pdf(
    review_result: Dict[str, Any],
    file_name: str,
    reviewed_at: Optional[datetime] = None,
) -> bytes:
    """
    生成合同审查报告 PDF。

    :param review_result: 审查结果 {risk_level, risks: [...], summary}
    :param file_name: 被审查的合同原始文件名
    :param reviewed_at: 审查时间（不传则使用当前时间）
    :return: PDF 文件的二进制内容
    """
    styles = _build_styles()
    reviewed_at = reviewed_at or datetime.now()

    risk_level = str(review_result.get("risk_level", "未知"))
    risks: List[Dict[str, Any]] = review_result.get("risks") or []
    summary = str(review_result.get("summary", "") or "")

    # 统计高/中/低风险数量
    counts = {"高": 0, "中": 0, "低": 0}
    for r in risks:
        lv = str(r.get("level", "中"))
        counts[lv] = counts.get(lv, 0) + 1

    # -------- 组装文档元素 --------
    story = []

    # 报告标题区
    story.append(Paragraph("合同风险审查报告", styles["title"]))
    story.append(Paragraph("法宝 · AI 法律助手", styles["subtitle"]))
    story.append(Spacer(1, 6))
    # 标题下的金色装饰线
    story.append(HRFlowable(width="30%", thickness=2, color=GOLD, spaceAfter=14))

    # 审查对象信息表
    info_tbl = Table(
        [
            [Paragraph("<b>审查文件</b>", styles["label"]), Paragraph(_clean(file_name), styles["body"])],
            [Paragraph("<b>审查时间</b>", styles["label"]),
             Paragraph(reviewed_at.strftime("%Y 年 %m 月 %d 日 %H:%M"), styles["body"])],
        ],
        colWidths=[3 * cm, None],
    )
    info_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(info_tbl)

    # 总体风险等级区：徽章 + 统计
    story.append(Paragraph("一、总体风险评级", styles["section"]))
    overall_color = RISK_COLORS.get(risk_level, colors.grey)
    overall_cell = Paragraph(
        f"<font color='white'><b>总体风险：{_clean(risk_level)}</b></font>",
        ParagraphStyle("ob", fontName=_FONT_NAME, fontSize=11, leading=16, alignment=1),
    )
    overall_badge = Table([[overall_cell]], colWidths=[4 * cm], rowHeights=[0.8 * cm])
    overall_badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), overall_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [5, 5, 5, 5]),
    ]))

    # 风险统计条
    stat_style = ParagraphStyle("stat", fontName=_FONT_NAME, fontSize=10.5, leading=15)
    stat_cells = [
        Paragraph(
            f"<font color='#c0392b'><b>高风险 {counts.get('高', 0)} 项</b></font>"
            f"&nbsp;&nbsp;&nbsp;"
            f"<font color='#e67e22'><b>中风险 {counts.get('中', 0)} 项</b></font>"
            f"&nbsp;&nbsp;&nbsp;"
            f"<font color='#27ae60'><b>低风险 {counts.get('低', 0)} 项</b></font>",
            stat_style,
        )
    ]
    stat_tbl = Table([[overall_badge, stat_cells[0]]], colWidths=[4.4 * cm, None])
    stat_tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]))
    story.append(stat_tbl)

    # 总体审查意见
    if summary:
        story.append(Spacer(1, 8))
        story.append(Paragraph(_clean(summary), styles["body"]))

    # 逐条风险详情
    story.append(Paragraph(f"二、风险条款详情（共 {len(risks)} 项）", styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e5e9f0"), spaceAfter=10))

    if risks:
        for idx, risk in enumerate(risks, start=1):
            story.extend(_risk_card(idx, risk, styles))
    else:
        story.append(Paragraph("未识别出明显的风险条款。", styles["body"]))

    # 页脚免责声明
    story.append(Spacer(1, 18))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#e5e9f0")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "免责声明：本报告由 AI 智能审查生成，仅供参考，不构成正式法律意见。"
        "重要合同建议咨询执业律师后签署。",
        ParagraphStyle("disclaimer", fontName=_FONT_NAME, fontSize=9, leading=14,
                       textColor=TEXT_GREY),
    ))

    # -------- 生成 PDF 到内存 --------
    from io import BytesIO

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        title="合同风险审查报告",
        author="法宝-AI法律助手",
    )
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
