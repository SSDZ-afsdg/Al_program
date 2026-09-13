<!-- AppHeader.vue —— 顶部导航栏 -->
<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { user, isLoggedIn, logout } = useAuth()

function goLogin() { router.push('/login') }

function handleLogout() {
  logout()
  ElMessage.success('已退出登录')
  router.push('/')
}
</script>

<template>
  <el-header class="app-header">
    <div class="header-inner">
      <router-link to="/" class="brand">
        <el-icon class="brand-logo" :size="34"><Balance /></el-icon>
        <span class="brand-name">法宝</span>
        <span class="brand-sub">AI法律助手</span>
      </router-link>

      <div class="nav-right">
        <nav class="nav-links">
          <router-link to="/ai-consult" class="nav-item" active-class="nav-item--active">AI法律咨询</router-link>
          <router-link to="/doc-generate" class="nav-item" active-class="nav-item--active">文书生成</router-link>
          <router-link to="/contract-review" class="nav-item" active-class="nav-item--active">合同审查</router-link>
        </nav>

        <div class="auth-area">
          <el-button v-if="!isLoggedIn" text class="login-btn" @click="goLogin">登录</el-button>
          <el-dropdown v-else @command="handleLogout">
            <span class="user-name">
              <el-icon><UserFilled /></el-icon>
              {{ user?.username }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
  </el-header>
</template>

<script>
export default { name: 'AppHeader' }
</script>

<style scoped>
.app-header {
  background: var(--color-primary);
  height: 64px;
  border-bottom: 2px solid var(--color-gold);
  position: sticky;
  top: 0;
  z-index: 100;
}
.header-inner {
  max-width: var(--container-width);
  margin: 0 auto;
  height: 100%;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand { display: flex; align-items: center; gap: 10px; }
.brand-logo { color: var(--color-gold); }
.brand-name { font-size: 22px; font-weight: 700; color: #fff; letter-spacing: 2px; }
.brand-sub { font-size: 13px; color: rgba(255,255,255,0.6); padding-left: 10px; border-left: 1px solid rgba(255,255,255,0.3); }

.nav-right { display: flex; align-items: center; gap: 20px; }
.nav-links { display: flex; align-items: center; gap: 8px; }
.nav-item {
  padding: 8px 18px; font-size: 15px; color: rgba(255,255,255,0.85);
  border-radius: 6px; transition: all 0.25s ease;
}
.nav-item:hover { color: var(--color-gold); background: rgba(255,255,255,0.08); }
.nav-item--active { color: var(--color-gold); font-weight: 600; background: rgba(201,169,110,0.15); }

.auth-area { display: flex; align-items: center; min-width: 70px; justify-content: flex-end; }
.login-btn { color: var(--color-gold) !important; font-size: 15px; padding: 8px 16px; }
.login-btn:hover { background: rgba(201,169,110,0.15); }
.user-name {
  display: flex; align-items: center; gap: 6px; color: rgba(255,255,255,0.9);
  cursor: pointer; font-size: 14px; padding: 6px 12px; border-radius: 6px; transition: all 0.25s ease;
}
.user-name:hover { background: rgba(255,255,255,0.1); }

@media (max-width: 768px) {
  .brand-sub { display: none; }
  .nav-item { padding: 8px 10px; font-size: 14px; }
  .nav-right { gap: 10px; }
}
</style>
