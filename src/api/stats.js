// stats.js —— 使用统计相关 API
import request from '@/utils/request'

/** 获取当前用户的使用统计（对话/消息/文书/合同数 + 近7天活跃数据） */
export function getSummary() {
  return request({ url: '/stats/summary', method: 'get' })
}
