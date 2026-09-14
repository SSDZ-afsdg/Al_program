// document.js —— 文书生成 API
import request from '@/utils/request'

export function generateDocument(data) {
  return request({ url: '/documents/generate', method: 'post', data })
}

export function listDocuments() {
  return request({ url: '/documents/list', method: 'get' })
}

export function getDocument(id) {
  return request({ url: `/documents/${id}`, method: 'get' })
}

/**
 * 导出文书记录为 Word 文件
 * @param {number} id - 文书记录 ID
 * @returns {Promise<Blob>} Word 文件二进制流（responseType: blob 直通返回）
 */
export function exportDocumentWord(id) {
  return request({
    url: `/documents/${id}/export`,
    method: 'get',
    responseType: 'blob',
  })
}
