// auth.js —— 认证相关 API
import request from '@/utils/request'

export function register(data) {
  return request({ url: '/auth/register', method: 'post', data })
}

export function login(data) {
  return request({ url: '/auth/login', method: 'post', data })
}

export function getCurrentUser() {
  return request({ url: '/auth/me', method: 'get' })
}
