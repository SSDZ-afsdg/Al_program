"""
markdown_to_docx.py —— Markdown 文本转 Word（.docx）工具

用途：将 AI 生成的法律文书（Markdown 格式）转换为排版规范的 Word 文档，
供用户下载后直接打印 / 编辑使用。

排版规则（参照中文法律文书习惯）：
- 文书主标题：二号加粗、居中
- 正文：仿宋_GB2312（回退宋体）、小四（12pt）、首行缩进 2 字符、1.5 倍行距
- 支持的 Markdown 元素：#/##/### 标题、**粗体**、> 引用、- / 1. 列表、--- 分隔线

依赖：python-docx（项目 requirements.txt 已包含）
"""

import re
from typing import List, Optional, Tuple

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

# 正文使用的中文字体（优先仿宋，符合公文习惯）
BODY_FONT = "仿宋_GB2312"
# 标题使用的中文字体
HEADING_FONT = "黑体"

# 行内 Markdown 粗体语法：**内容** 或 __内容__
_BOLD_PATTERN = re.compile(r"(\*\*(.+?)\*\*|__(.+?)__)")


def _set_run_font(run, chinese_font: str, size: Optional[Pt] = None, bold: Optional[bool] = None) -> None:
    """
    设置文本 run 的字体（中英文分开设置）。

    python-docx 中 run.font.name 只影响西文字体，
    中文字体需要通过 XML 的 w:eastAsia 属性单独设置。
    """
    run.font.name = "Times New Roman"  # 西文/数字使用 Times New Roman
    # 通过底层 XML 设置中文字体
    run._element.rPr.rFonts.set(qn("w:eastAsia"), chinese_font)
    if size is not None:
        run.font.size = size
    if bold is not None:
        run.bold = bold


def _setup_document(doc: Document) -> None:
    """初始化文档全局样式：页边距、默认字体、行距。"""
    # 页边距：上下 2.54cm、左右 3.17cm（Word 中文默认值）
    for section in doc.sections:
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(3.17)
        section.right_margin = Cm(3.17)

    # 修改默认 Normal 样式，保证后续段落继承统一的字体与行距
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)  # 小四
    # 默认样式同样需要设置中文字体
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)


def _add_main_title(doc: Document, title: str) -> None:
    """添加文书主标题：二号（22pt）加粗、居中。"""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_after = Pt(18)  # 标题与正文之间留白
    run = para.add_run(title)
    _set_run_font(run, HEADING_FONT, size=Pt(22), bold=True)


def _add_body_paragraph(doc: Document, text: str, indent: bool = True) -> None:
    """
    添加正文段落：解析行内 **粗体** 语法，普通文本首行缩进 2 字符。

    :param indent: 是否首行缩进（引用/列表等特殊段落不缩进）
    """
    para = doc.add_paragraph()
    para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    if indent:
        # 首行缩进 2 字符（中文习惯：缩进两个汉字宽度）
        para.paragraph_format.first_line_indent = Pt(24)  # 12pt 字号 × 2

    # 按 **粗体** 语法切分行内内容，逐段生成 run
    _add_inline_runs(para, text)


def _add_inline_runs(para, text: str) -> None:
    """解析一行文本中的 **粗体** 片段，生成对应的普通/加粗 run。"""
    parts: List[Tuple[str, bool]] = []  # (文本片段, 是否加粗)
    pos = 0
    for match in _BOLD_PATTERN.finditer(text):
        # 粗体标记之前的普通文本
        if match.start() > pos:
            parts.append((text[pos:match.start()], False))
        # group(2)/group(3)：**xxx** 或 __xxx__ 内部的真实文本
        bold_text = match.group(2) or match.group(3) or ""
        parts.append((bold_text, True))
        pos = match.end()
    # 末尾剩余的普通文本
    if pos < len(text):
        parts.append((text[pos:], False))

    # 全部为普通文本时（无粗体），直接生成单个 run
    if not parts:
        parts = [(text, False)]

    for segment, is_bold in parts:
        if not segment:
            continue
        run = para.add_run(segment)
        _set_run_font(run, BODY_FONT, bold=is_bold if is_bold else None)


def _add_quote(doc: Document, text: str) -> None:
    """添加引用段落：左缩进 + 灰色小字（法律文书中常用于备注说明）。"""
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.74)
    para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    run = para.add_run(text)
    _set_run_font(run, BODY_FONT, size=Pt(10.5))


def _add_list_item(doc: Document, text: str, ordered: bool) -> None:
    """添加列表项：无序用圆点前缀，有序用编号前缀（保持中文文书简洁风格）。"""
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.74)
    para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    prefix = "• " if not ordered else ""
    # 有序列表的编号已在解析时提取到 text 中，无序列表补圆点前缀
    run = para.add_run(f"{prefix}{text}")
    _set_run_font(run, BODY_FONT)


def markdown_to_docx(md_text: str, title: Optional[str] = None) -> Document:
    """
    将 Markdown 文本转换为 python-docx 文档对象。

    :param md_text: Markdown 格式的文书内容
    :param title: 文书主标题（如"民事起诉状"），为空则不生成主标题行
    :return: python-docx 的 Document 对象（可继续编辑或直接保存）
    """
    doc = Document()
    _setup_document(doc)

    # 生成主标题
    if title:
        _add_main_title(doc, title)

    # 逐行解析 Markdown 并写入文档
    for raw_line in md_text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        # 空行：跳过（段落间距由 space_after 控制，避免产生大量空白）
        if not stripped:
            continue

        # 分隔线：--- / *** / ___ → 转为居中的短横线装饰行
        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            hr = doc.add_paragraph()
            hr.alignment = WD_ALIGN_PARAGRAPH.CENTER
            hr_run = hr.add_run("────────")
            _set_run_font(hr_run, BODY_FONT, size=Pt(10))
            continue

        # 标题：# / ## / ### → 一、二、三级标题（逐级缩小、加粗、黑体）
        heading_match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))          # 几级标题
            heading_text = heading_match.group(2).strip()
            # 字号映射：h1→16pt，h2→14pt，h3→13pt，h4→12pt
            size_map = {1: Pt(16), 2: Pt(14), 3: Pt(13), 4: Pt(12)}
            para = doc.add_paragraph()
            para.paragraph_format.space_before = Pt(10)
            para.paragraph_format.space_after = Pt(6)
            # 一级标题居中（如文书内的小节标题），其余左对齐
            if level == 1:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run(heading_text)
            _set_run_font(run, HEADING_FONT, size=size_map.get(level, Pt(12)), bold=True)
            continue

        # 引用：> 内容
        quote_match = re.match(r"^>\s?(.*)$", stripped)
        if quote_match:
            _add_quote(doc, quote_match.group(1).strip())
            continue

        # 无序列表：- 内容 或 * 内容
        ul_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if ul_match:
            _add_list_item(doc, ul_match.group(1).strip(), ordered=False)
            continue

        # 有序列表：1. 内容（保留原文编号，直接作为正文带编号段落）
        ol_match = re.match(r"^(\d+)[.、]\s*(.*)$", stripped)
        if ol_match:
            _add_list_item(doc, f"{ol_match.group(1)}. {ol_match.group(2)}", ordered=True)
            continue

        # 普通段落：首行缩进 + 解析行内粗体
        _add_body_paragraph(doc, stripped)

    return doc


def save_docx(md_text: str, file_path: str, title: Optional[str] = None) -> str:
    """
    便捷方法：Markdown 转 Word 并保存到指定路径。

    :param md_text: Markdown 格式的文书内容
    :param file_path: 保存路径（以 .docx 结尾）
    :param title: 文书主标题
    :return: 实际保存的文件路径
    """
    doc = markdown_to_docx(md_text, title=title)
    doc.save(file_path)
    return file_path
