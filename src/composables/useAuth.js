// useAuth.js —— 认证状态管理
import { reactive, computed } from 'vue'
import { login as loginApi, register as registerApi } from '@/api/auth'

// 模块级响应式状态（全局共享）
const state = reactive({
  user: null,
  token: '',
})

// 初始化：从 localStorage 恢复登录态
const savedToken = localStorage.getItem('fabao_token')
const savedUser = localStorage.getItem('fabao_user')
if (savedToken) {
  state.token = savedToken
  state.user = savedUser ? JSON.parse(savedUser) : null
}

function persist() {
  if (state.token) localStorage.setItem('fabao_token', state.token)
  if (state.user) localStorage.setItem('fabao_user', JSON.stringify(state.user))
}

function clear() {
  state.user = null
  state.token = ''
  localStorage.removeItem('fabao_token')
  localStorage.removeItem('fabao_user')
}

export function useAuth() {
  const isLoggedIn = computed(() => !!state.token)

  async function login(payload) {
    const res = await loginApi(payload)
    state.token = res.access_token
    state.user = res.user
    persist()
  }

  async function register(payload) {
    await registerApi(payload)
  }

  function logout() {
    clear()
  }

  return {
    user: computed(() => state.user),
    token: computed(() => state.token),
    isLoggedIn,
    login,
    register,
    logout,
  }
}
