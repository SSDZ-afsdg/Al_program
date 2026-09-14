// router/index.js —— Vue Router 路由配置
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', meta: { title: '首页 - 法宝AI法律助手' }, component: () => import('@/views/HomePage.vue') },
  { path: '/login', name: 'Login', meta: { title: '登录 - 法宝AI法律助手' }, component: () => import('@/views/Login.vue') },
  { path: '/profile', name: 'Profile', meta: { title: '个人中心 - 法宝AI法律助手', requiresAuth: true }, component: () => import('@/views/Profile.vue') },
  { path: '/ai-consult', name: 'AiConsult', meta: { title: 'AI法律咨询 - 法宝AI法律助手', requiresAuth: true }, component: () => import('@/views/AiConsult.vue') },
  { path: '/doc-generate', name: 'DocGenerate', meta: { title: '文书生成 - 法宝AI法律助手', requiresAuth: true }, component: () => import('@/views/DocGenerate.vue') },
  { path: '/contract-review', name: 'ContractReview', meta: { title: '合同审查 - 法宝AI法律助手', requiresAuth: true }, component: () => import('@/views/ContractReview.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫：页面标题 + 登录鉴权
router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '法宝 - AI法律助手'
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('fabao_token')
    if (!token) {
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }
  }
  next()
})

export default router
