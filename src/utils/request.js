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
    // 文件流响应（responseType: 'blob'，用于 Word/PDF 导出下载）：
    // 不做 {code, message, data} 解包，直接返回 Blob 交给调用方保存
    if (response.config.responseType === 'blob') {
      return response.data
    }
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
  // 注意：文件流接口失败时错误响应体同样是 Blob，需要异步读取才能拿到后端 message，
  // 因此错误回调声明为 async，避免出现"只弹一句英文、用户以为没反应"的体验
  async (error) => {
    let msg = error.response?.data?.message || error.message || '网络异常，请稍后重试'

    // blob 请求失败：错误体是 Blob（FastAPI/全局异常处理器返回的 JSON），
    // 同步访问 .message 得到 undefined，这里读出文本解析出真实错误信息
    const errData = error.response?.data
    if (errData instanceof Blob && errData.type && errData.type.includes('application/json')) {
      try {
        const errObj = JSON.parse(await errData.text())
        msg = errObj.message || msg
      } catch (_) {
        /* 错误体不是合法 JSON 时沿用默认提示 */
      }
    }

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
