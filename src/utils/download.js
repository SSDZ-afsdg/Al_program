// download.js —— 文件下载工具
// 将后端返回的 Blob 文件流保存为本地文件（Word / PDF 导出等场景复用）

import { ElMessage } from 'element-plus'

/**
 * 触发浏览器下载一个 Blob 文件
 * @param {Blob} blob - 文件二进制流
 * @param {string} filename - 保存的文件名（可含中文）
 */
export function saveBlobAs(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  // 延迟释放，避免部分浏览器在下载未开始前就回收了 URL
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

/**
 * 从响应头解析下载文件名（后端以 RFC 5987 filename*=UTF-8'' 返回中文文件名）
 * @param {Response|Object} headers - axios 响应头对象
 * @param {string} fallback - 解析失败时的默认文件名
 * @returns {string}
 */
export function parseFilename(headers, fallback = '下载文件') {
  const disposition = headers?.['content-disposition'] || headers?.get?.('content-disposition') || ''
  // 优先匹配 filename*=UTF-8''xxx（URL 编码的中文文件名）
  const starMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (starMatch) {
    try { return decodeURIComponent(starMatch[1]) } catch (_) { /* 编码异常则继续降级 */ }
  }
  const plainMatch = disposition.match(/filename="?([^";]+)"?/i)
  if (plainMatch) return plainMatch[1]
  return fallback
}

/**
 * 校验 Blob 是否为后端返回的错误 JSON（业务异常时响应也是 blob 包装）
 * 是错误则提示并抛出异常；正常文件流原样返回
 * @param {Blob} blob
 */
export async function throwIfBlobError(blob) {
  // JSON 错误响应的 MIME 为 application/json，正常文件流不会是 json
  if (blob && blob.type && blob.type.includes('application/json')) {
    const text = await blob.text()
    let msg = '下载失败'
    try {
      msg = JSON.parse(text).message || msg
    } catch (_) { /* JSON 解析失败则用默认提示 */ }
    ElMessage.error(msg)
    throw new Error(msg)
  }
  return blob
}
