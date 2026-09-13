// request.js —— Axios 请求封装
// 1. 创建 axios 实例，baseURL 指向 /api/v1（配合 vite 代理）
// 2. 请求拦截器：自动注入 JWT
// 3. 响应拦截器：统一解包 { code, message, data }，401 自动登出

import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const TOKEN_KEY = 'fabao_token'

const service = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,  // AI 生成耗时较长（文书/合同审查约 30s），设为 2 分钟
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const res = response.data
    // 业务状态码非 200 视为失败
    if (res.code && res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      if (res.code === 401) {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem('fabao_user')
        router.push('/login')
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res.data
  },
  (error) => {
    const msg = error.response?.data?.message || error.message || '网络异常，请稍后重试'
    ElMessage.error(msg)
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem('fabao_user')
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default service
