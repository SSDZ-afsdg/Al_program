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
