// auth.js —— 认证与个人中心相关 API
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

/** 修改个人资料（用户名 / 邮箱 / 手机号，全部可选） */
export function updateProfile(data) {
  return request({ url: '/auth/profile', method: 'patch', data })
}

/** 修改密码（需校验旧密码） */
export function changePassword(data) {
  return request({ url: '/auth/password', method: 'put', data })
}

/**
 * 上传 / 更新头像
 * 注意：头像接口走 multipart/form-data，由 axios 自动处理 Content-Type 与 boundary；
 * 切勿手动设置 'Content-Type: multipart/form-data'，否则会丢失 boundary。
 */
export function uploadAvatar(file) {
  const form = new FormData()
  form.append('file', file)
  return request({ url: '/auth/avatar', method: 'post', data: form })
}
