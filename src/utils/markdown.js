// markdown.js —— 统一的 Markdown 渲染工具
// 职责：
// 1. 用 marked 将 Markdown 文本解析为 HTML；
// 2. 用 DOMPurify 清洗 HTML，移除 <script>/onerror/事件处理器等 XSS 风险；
// 3. 暴露 renderMarkdown(text) 供所有 v-html 场景复用（AI 咨询、文书、合同审查等）。
//
// 安全说明：
// - 严禁直接对 AI 返回内容用 v-html，必须先经过本函数处理；
// - DOMPurify 默认配置已足以拦截常见 XSS 向量；
// - 如需允许特定标签（如 iframe 视频），可在 ALLOWED_TAGS 显式声明，不要默认放开。

import { marked } from 'marked'
import DOMPurify from 'dompurify'

// marked 全局配置：开启 GFM（表格、删除线）与 breaks（换行渲染）
marked.setOptions({ breaks: true, gfm: true })

/**
 * 将 Markdown 文本安全渲染为可插入 v-html 的 HTML 字符串
 * @param {string} content - 原始 Markdown 文本
 * @returns {string} 经 DOMPurify 清洗后的 HTML
 */
export function renderMarkdown(content) {
  if (!content) return ''
  // 1) Markdown -> HTML
  const rawHtml = marked.parse(content)
  // 2) HTML -> 安全 HTML（拦截 <script>、javascript:、on* 事件等）
  return DOMPurify.sanitize(rawHtml, {
    // 允许常见排版标签；如未来需要 iframe（嵌入视频），可在此处显式加入
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'br', 'hr', 'blockquote',
      'strong', 'em', 'del', 's', 'sub', 'sup', 'u',
      'ul', 'ol', 'li',
      'a', 'img',
      'code', 'pre', 'span',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'div', 'span',
    ],
    // 允许的属性：a[href|title|target]、img[src|alt|title]、code[class]、pre[class]
    ALLOWED_ATTR: ['href', 'title', 'target', 'src', 'alt', 'class', 'colspan', 'rowspan'],
    // 强制所有 a 链接在新标签打开，并加上 rel=noopener 防止反向 tabnabbing
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['style', 'iframe', 'form', 'input', 'button', 'textarea'],
    FORBID_ATTR: ['style', 'onerror', 'onload', 'onclick', 'onmouseover'],
  })
}

/**
 * 给 DOMPurify 添加钩子：所有 <a> 自动追加 target=_blank + rel=noopener noreferrer
 * 在 import 本模块时即生效，全局一次注册即可。
 */
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  if (node.tagName === 'A' && node.getAttribute('href')) {
    node.setAttribute('target', '_blank')
    node.setAttribute('rel', 'noopener noreferrer')
  }
})
