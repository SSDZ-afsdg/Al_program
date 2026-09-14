// chat.js —— AI 法律咨询 API
import request from '@/utils/request'

export function listConversations() {
  return request({ url: '/chat/conversations', method: 'get' })
}

export function createConversation(data = {}) {
  return request({ url: '/chat/conversations', method: 'post', data })
}

/** 重命名对话（PATCH） */
export function updateConversation(id, data) {
  return request({ url: `/chat/conversations/${id}`, method: 'patch', data })
}

export function deleteConversation(id) {
  return request({ url: `/chat/conversations/${id}`, method: 'delete' })
}

/**
 * 游标分页获取消息列表
 * @param {number} id - 对话 ID
 * @param {object} params - { limit?: 20, before_id?: number }（before_id 用于加载更早消息）
 * @returns {Promise<{items: Array, has_more: boolean}>}
 */
export function listMessages(id, params = {}) {
  return request({ url: `/chat/conversations/${id}/messages`, method: 'get', params })
}

export function sendMessage(id, data) {
  return request({ url: `/chat/conversations/${id}/messages`, method: 'post', data })
}

/**
 * 流式发送消息（SSE）
 * @param {number} id - 对话 ID
 * @param {object} data - { content: '用户问题' }
 * @param {object} callbacks - { onMessage(chunk), onDone(messageId), onError(errMsg) }
 * @returns {Promise<void>}
 *
 * 说明：SSE 流不经过 axios 拦截器，直接用 fetch + ReadableStream 解析，
 * 后端以 text/event-stream 推送 data: {json} 片段。
 */
export async function sendMessageStream(id, data, callbacks) {
  const token = localStorage.getItem('fabao_token') || ''
  const response = await fetch(`/api/v1/chat/conversations/${id}/messages/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    let errMsg = `请求失败（${response.status}）`
    try {
      const err = await response.json()
      errMsg = err.message || errMsg
    } catch (_) { /* ignore */ }
    callbacks.onError?.(errMsg)
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE 以 \n\n 分隔事件
    const events = buffer.split('\n\n')
    buffer = events.pop() // 最后一段可能不完整，保留到下次处理

    for (const event of events) {
      const line = event.trim()
      if (!line.startsWith('data:')) continue
      const dataStr = line.slice(5).trim()
      if (!dataStr) continue
      try {
        const obj = JSON.parse(dataStr)
        if (obj.error) {
          callbacks.onError?.(obj.error)
          return
        }
        if (obj.done) {
          callbacks.onDone?.(obj.message_id)
          return
        }
        if (obj.content) {
          callbacks.onMessage?.(obj.content)
        }
      } catch (_) { /* 忽略解析失败的片段 */ }
    }
  }
}
