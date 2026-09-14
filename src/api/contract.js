// contract.js —— 合同审查 API
import request from '@/utils/request'

export function uploadContract(file) {
  const formData = new FormData()
  formData.append('file', file)
  // 注意：不要手动设置 Content-Type！
  // 当 data 为 FormData 时，axios 会自动设置带 boundary 的 multipart/form-data，
  // 手动设置反而会丢失 boundary，导致后端无法解析文件字段。
  return request({
    url: '/contracts/upload',
    method: 'post',
    data: formData,
  })
}

export function reviewContract(id) {
  return request({ url: `/contracts/review/${id}`, method: 'post' })
}

export function listContracts() {
  return request({ url: '/contracts/list', method: 'get' })
}

/** 获取合同记录详情（含原文全文与审查结果，用于风险定位高亮） */
export function getContractDetail(id) {
  return request({ url: `/contracts/${id}`, method: 'get' })
}

/**
 * 导出审查报告 PDF
 * @param {number} id - 合同记录 ID
 * @returns {Promise<Blob>} PDF 文件二进制流（responseType: blob 直通返回）
 */
export function exportReviewPdf(id) {
  return request({
    url: `/contracts/${id}/export-pdf`,
    method: 'get',
    responseType: 'blob',
  })
}
