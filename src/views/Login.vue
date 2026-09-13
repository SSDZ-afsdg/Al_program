<!-- Login.vue —— 登录 / 注册页 -->
<script setup>
import { ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const router = useRouter()
const { login, register } = useAuth()

const activeTab = ref('login')

const loginForm = reactive({ username: '', password: '' })
const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerForm = reactive({ username: '', email: '', password: '' })
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度 3-50 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

const submitting = ref(false)

async function handleLogin() {
  try {
    submitting.value = true
    await login({ ...loginForm })
    ElMessage.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) { /* 全局已提示 */ }
  finally { submitting.value = false }
}

async function handleRegister() {
  try {
    submitting.value = true
    await register({ ...registerForm })
    ElMessage.success('注册成功，请使用新账号登录')
    loginForm.username = registerForm.username
    registerForm.email = ''
    registerForm.password = ''
    activeTab.value = 'login'
  } catch (e) { /* 全局已提示 */ }
  finally { submitting.value = false }
}
</script>

<template>
  <div class="login-page">
    <div class="login-bg"></div>
    <el-card class="login-card" shadow="always">
      <div class="brand">
        <el-icon :size="36" class="brand-icon"><Balance /></el-icon>
        <span class="brand-name">法宝</span>
        <span class="brand-sub">AI法律助手</span>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" :rules="loginRules" label-position="top" @keyup.enter="handleLogin">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" :prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" size="large" show-password />
            </el-form-item>
            <el-button type="primary" size="large" class="submit-btn" :loading="submitting" @click="handleLogin">登录</el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" :rules="registerRules" label-position="top" @keyup.enter="handleRegister">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="registerForm.username" placeholder="3-50 个字符" :prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="registerForm.email" placeholder="请输入邮箱" :prefix-icon="Message" size="large" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="至少 6 位" :prefix-icon="Lock" size="large" show-password />
            </el-form-item>
            <el-button type="primary" size="large" class="submit-btn" :loading="submitting" @click="handleRegister">注册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <p class="login-tip">
        {{ activeTab === 'login' ? '还没有账号？' : '已有账号？' }}
        <a class="login-switch" @click="activeTab = activeTab === 'login' ? 'register' : 'login'">
          {{ activeTab === 'login' ? '立即注册' : '返回登录' }}
        </a>
      </p>
    </el-card>
  </div>
</template>

<script>
import { User, Lock, Message } from '@element-plus/icons-vue'
export default { name: 'Login', components: { User, Lock, Message } }
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: calc(100vh - 64px - 200px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  overflow: hidden;
}
.login-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--color-primary-dark), var(--color-primary), var(--color-primary-light));
  opacity: 0.08;
  z-index: -1;
}
.login-card { width: 100%; max-width: 420px; border-radius: 12px; }
.brand { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 16px; }
.brand-icon { color: var(--color-gold); }
.brand-name { font-size: 24px; font-weight: 700; color: var(--color-primary); letter-spacing: 2px; }
.brand-sub { font-size: 13px; color: var(--color-text-secondary); padding-left: 8px; border-left: 1px solid var(--color-border); }
.login-tabs { margin-top: 16px; }
.submit-btn {
  width: 100%; margin-top: 8px;
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-light);
  --el-button-hover-border-color: var(--color-primary-light);
}
.login-tip { text-align: center; margin-top: 16px; font-size: 13px; color: var(--color-text-secondary); }
.login-switch { color: var(--color-primary); cursor: pointer; margin-left: 4px; }
.login-switch:hover { text-decoration: underline; }
</style>
