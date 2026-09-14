<!-- Profile.vue —— 个人中心页 -->
<!-- 整体结构：用户卡片（头像 + 信息）→ 使用统计区（数字 + 近7天趋势图）→ 资料修改 → 密码修改 -->
<script setup>
/**
 * 个人中心组件
 *
 * 页面结构（从上到下）：
 * 1. 顶部用户卡片：头像（可点击上传新头像）、用户名、邮箱、注册时间
 * 2. 使用统计区：4 个数字卡片 + 近 7 天活跃趋势条形图
 * 3. 资料修改卡片：用户名、邮箱、手机号
 * 4. 密码修改卡片：旧密码、新密码、确认密码
 *
 * 视觉风格：与全站保持一致，深蓝主色 + 金色点缀
 */

import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuth } from '@/composables/useAuth'
import {
  updateProfile as updateProfileApi,
  changePassword as changePasswordApi,
  uploadAvatar as uploadAvatarApi,
} from '@/api/auth'
import { getSummary } from '@/api/stats'

const { user, setUser } = useAuth()

// ============================================================
// 一、用户卡片区：头像与基本信息
// ============================================================
const avatarUploading = ref(false)

/** 头像完整 URL：本地后端返回相对路径，前端拼接 baseURL 后才能正确展示 */
const avatarUrl = computed(() => {
  const rel = user.value?.avatar_url
  if (!rel) return ''
  // 后端挂载 /uploads 静态目录，相对路径以 uploads/ 开头，前端补 "/"
  if (rel.startsWith('http')) return rel
  return rel.startsWith('/') ? rel : '/' + rel
})

/** 首字母作为头像兜底显示（无头像时使用 el-avatar 显示用户名首字） */
const avatarInitial = computed(() => (user.value?.username || '?').charAt(0).toUpperCase())

/** 注册时间格式化（仅日期） */
const registeredAt = computed(() => {
  const iso = user.value?.created_at
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN')
})

/** 最近登录时间格式化（含时分） */
const lastLoginAt = computed(() => {
  const iso = user.value?.last_login_at
  if (!iso) return '暂无记录'
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
})

/** 头像上传：选择文件后立即上传 */
async function handleAvatarChange(file) {
  const raw = file.raw || file
  // 前端预校验：类型 + 大小
  const ext = (raw.name.split('.').pop() || '').toLowerCase()
  if (!['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext)) {
    ElMessage.error('仅支持 png / jpg / jpeg / webp / gif 格式')
    return false
  }
  if (raw.size > 2 * 1024 * 1024) {
    ElMessage.error('头像大小不能超过 2MB')
    return false
  }

  avatarUploading.value = true
  try {
    const res = await uploadAvatarApi(raw)
    // 后端返回 avatar_url，前端立即更新本地用户信息（避免再次拉取 /me）
    setUser({ ...user.value, avatar_url: res.avatar_url })
    ElMessage.success('头像更新成功')
  } catch (e) { /* 全局已提示 */ }
  finally { avatarUploading.value = false }
  return false
}

// ============================================================
// 二、使用统计区
// ============================================================
const stats = ref({
  conversation_count: 0,
  message_count: 0,
  document_count: 0,
  contract_count: 0,
  reviewed_contract_count: 0,
  recent_activity: [],
})
const loadingStats = ref(false)

/** 统计数字卡片配置：图标 + 标题 + 字段名 + 颜色 */
const statCards = computed(() => [
  { icon: 'ChatDotRound', label: '法律咨询对话', value: stats.value.conversation_count, color: '#1a3a5c' },
  { icon: 'Comment', label: '消息总数', value: stats.value.message_count, color: '#3498db' },
  { icon: 'Document', label: '生成文书', value: stats.value.document_count, color: '#c9a96e' },
  { icon: 'View', label: '上传合同', value: stats.value.contract_count, color: '#9b59b6' },
])

/** 已审查合同数：单独展示在合同卡片的子标签 */
const reviewedCount = computed(() => stats.value.reviewed_contract_count)

/** 近 7 天活跃数据的最大值，用于柱状图高度计算 */
const maxActivity = computed(() => {
  const counts = stats.value.recent_activity.map((x) => x.count)
  return Math.max(1, ...counts)  // 至少 1，避免除以 0
})

/** 周几标签：weekday 0=周一 ... 6=周日 */
const WEEKDAY_NAMES = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

/** 把 ISO 日期字符串转为"月/日"格式，用于柱状图 X 轴标签 */
function formatDateShort(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

async function loadStats() {
  loadingStats.value = true
  try {
    const res = await getSummary()
    stats.value = res
  } catch (e) { /* 全局已提示 */ }
  finally { loadingStats.value = false }
}

// ============================================================
// 三、资料修改区
// ============================================================
const profileForm = reactive({
  username: '',
  email: '',
  phone: '',
})
const profileRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度 3-50 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  phone: [
    { pattern: /^\d{11}$/, message: '手机号必须为 11 位数字', trigger: 'blur' },
  ],
}
const profileFormRef = ref(null)
const savingProfile = ref(false)

/** 初始化：拉取统计数据，并把当前用户信息回填到资料表单 */
function syncProfileFromUser() {
  if (!user.value) return
  profileForm.username = user.value.username || ''
  profileForm.email = user.value.email || ''
  profileForm.phone = user.value.phone || ''
}

async function handleSaveProfile() {
  if (!profileFormRef.value) return
  try {
    await profileFormRef.value.validate()
  } catch { return }

  savingProfile.value = true
  try {
    // 只提交发生变化的字段，避免覆盖空值
    const patch = {}
    if (profileForm.username !== user.value.username) patch.username = profileForm.username
    if (profileForm.email !== user.value.email) patch.email = profileForm.email
    // 手机号空串视为清空
    if ((profileForm.phone || '') !== (user.value.phone || '')) patch.phone = profileForm.phone || ''
    if (Object.keys(patch).length === 0) {
      ElMessage.info('资料未发生变化')
      return
    }
    const updated = await updateProfileApi(patch)
    setUser(updated)
    ElMessage.success('资料修改成功')
  } catch (e) { /* 全局已提示 */ }
  finally { savingProfile.value = false }
}

// ============================================================
// 四、密码修改区
// ============================================================
const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const pwdRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度 6-64 位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.new_password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}
const pwdFormRef = ref(null)
const savingPwd = ref(false)

async function handleChangePassword() {
  if (!pwdFormRef.value) return
  try {
    await pwdFormRef.value.validate()
  } catch { return }

  // 前端额外校验：新旧密码不能相同
  if (pwdForm.old_password === pwdForm.new_password) {
    ElMessage.warning('新密码不能与旧密码相同')
    return
  }

  savingPwd.value = true
  try {
    await changePasswordApi({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，下次登录请使用新密码')
    pwdFormRef.value.resetFields()
    // 修改密码后建议重新登录：弹窗确认后跳转登录页
    try {
      await ElMessageBox.confirm('密码已修改，建议重新登录以同步登录态，是否立即重新登录？', '提示', {
        type: 'warning',
        confirmButtonText: '重新登录',
        cancelButtonText: '稍后',
      })
      // 用户确认：清空本地登录态并跳转登录页
      const { logout } = useAuth()
      logout()
      // 跳转交给路由全局守卫触发（无 token 时会自动回到 /login）
      window.location.href = '/'
    } catch { /* 用户选择稍后再登录 */ }
  } catch (e) { /* 全局已提示 */ }
  finally { savingPwd.value = false }
}

// ============================================================
// 生命周期：初始化
// ============================================================
onMounted(() => {
  syncProfileFromUser()
  loadStats()
})
</script>

<template>
  <div class="profile-page">
    <!-- =====================================================
         一、用户卡片：头像 + 基本信息
         ===================================================== -->
    <section class="user-card">
      <div class="user-left">
        <el-upload
          :show-file-list="false"
          :auto-upload="false"
          :on-change="handleAvatarChange"
          accept=".png,.jpg,.jpeg,.webp,.gif"
          class="avatar-uploader"
        >
          <div class="avatar-wrapper" v-loading="avatarUploading">
            <el-avatar v-if="avatarUrl" :size="96" :src="avatarUrl" />
            <el-avatar v-else :size="96" class="avatar-fallback">{{ avatarInitial }}</el-avatar>
            <div class="avatar-mask">
              <el-icon><Camera /></el-icon>
              <span>更换头像</span>
            </div>
          </div>
        </el-upload>
        <p class="avatar-tip">点击头像更换（≤ 2MB）</p>
      </div>

      <div class="user-info">
        <h2 class="user-name">{{ user?.username }}</h2>
        <p class="user-email">
          <el-icon><Message /></el-icon>
          <span>{{ user?.email }}</span>
        </p>
        <p class="user-meta">
          <el-tag v-if="user?.phone" size="small" type="info">{{ user.phone }}</el-tag>
          <el-tag v-else size="small" type="info">未绑定手机</el-tag>
          <el-tag size="small" :type="user?.role === 'admin' ? 'danger' : 'success'">
            {{ user?.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
        </p>
        <div class="user-dates">
          <span>注册时间：{{ registeredAt || '—' }}</span>
          <span>最近登录：{{ lastLoginAt }}</span>
        </div>
      </div>
    </section>

    <!-- =====================================================
         二、使用统计区
         ===================================================== -->
    <section class="stats-section">
      <h3 class="section-title">
        <el-icon class="title-icon"><DataAnalysis /></el-icon>
        使用统计
      </h3>

      <div v-loading="loadingStats" class="stats-grid">
        <div v-for="card in statCards" :key="card.label" class="stat-card" :style="{ '--card-color': card.color }">
          <el-icon class="stat-icon" :size="28">
            <component :is="card.icon" />
          </el-icon>
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </div>

      <!-- 合同审查完成情况：单独一行小标签 -->
      <div class="contract-extra">
        <el-tag type="success" effect="plain">
          已完成审查：{{ reviewedCount }} 份 / 共 {{ stats.contract_count }} 份
        </el-tag>
      </div>

      <!-- 近 7 天活跃趋势柱状图（纯 CSS 实现，无第三方图表库依赖） -->
      <div class="activity-chart">
        <h4 class="chart-title">近 7 天活跃趋势</h4>
        <div class="chart-bars">
          <div v-for="item in stats.recent_activity" :key="item.date" class="bar-col">
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ height: (item.count / maxActivity * 100) + '%' }"
                :title="`${formatDateShort(item.date)}：${item.count} 次活跃`"
              >
                <span class="bar-value">{{ item.count }}</span>
              </div>
            </div>
            <div class="bar-label">
              <span class="bar-weekday">{{ WEEKDAY_NAMES[item.weekday] }}</span>
              <span class="bar-date">{{ formatDateShort(item.date) }}</span>
            </div>
          </div>
        </div>
        <p class="chart-tip">每日活跃 = 当日新增的对话 / 消息 / 文书 / 合同事件总数</p>
      </div>
    </section>

    <!-- =====================================================
         三、资料修改区
         ===================================================== -->
    <section class="form-section">
      <h3 class="section-title">
        <el-icon class="title-icon"><Edit /></el-icon>
        修改个人资料
      </h3>
      <el-form
        ref="profileFormRef"
        :model="profileForm"
        :rules="profileRules"
        label-width="100px"
        class="profile-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="profileForm.username" placeholder="3-50 个字符" :prefix-icon="User" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="profileForm.email" placeholder="请输入邮箱" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="profileForm.phone" placeholder="11 位手机号（可选）" :prefix-icon="Iphone" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingProfile" @click="handleSaveProfile">保存修改</el-button>
          <el-button @click="syncProfileFromUser">重置</el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- =====================================================
         四、密码修改区
         ===================================================== -->
    <section class="form-section">
      <h3 class="section-title">
        <el-icon class="title-icon"><Lock /></el-icon>
        修改密码
      </h3>
      <el-form
        ref="pwdFormRef"
        :model="pwdForm"
        :rules="pwdRules"
        label-width="100px"
        class="pwd-form"
      >
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入旧密码" :prefix-icon="Lock" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="6-64 位新密码" :prefix-icon="Key" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" :prefix-icon="Key" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="savingPwd" @click="handleChangePassword">修改密码</el-button>
          <el-button @click="pwdFormRef?.resetFields()">重置</el-button>
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<script>
// 注册图标组件：el-icon 内 <component :is="..."> 需要全局可用
import {
  Camera, Message, User, Iphone, Edit, Lock, Key, DataAnalysis,
  ChatDotRound, Comment, Document, View,
} from '@element-plus/icons-vue'

export default {
  name: 'Profile',
  components: {
    Camera, Message, User, Iphone, Edit, Lock, Key, DataAnalysis,
    ChatDotRound, Comment, Document, View,
  },
}
</script>

<style scoped>
.profile-page { max-width: 960px; margin: 0 auto; padding: 24px 20px 60px; }

/* ===== 用户卡片 ===== */
.user-card {
  display: flex; align-items: center; gap: 32px;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
  color: #fff; border-radius: 12px; padding: 32px; box-shadow: var(--shadow-card);
}
.user-left { display: flex; flex-direction: column; align-items: center; }
.avatar-uploader { cursor: pointer; }
.avatar-wrapper { position: relative; width: 96px; height: 96px; border-radius: 50%; overflow: hidden; cursor: pointer; }
.avatar-fallback { background: var(--color-gold); color: #fff; font-size: 32px; font-weight: 700; }
.avatar-mask {
  position: absolute; inset: 0; background: rgba(0,0,0,0.55);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  color: #fff; font-size: 12px; gap: 4px; opacity: 0; transition: opacity 0.25s;
}
.avatar-wrapper:hover .avatar-mask { opacity: 1; }
.avatar-tip { margin-top: 8px; font-size: 12px; color: rgba(255,255,255,0.7); }

.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 28px; font-weight: 700; margin: 0 0 12px; }
.user-email { display: flex; align-items: center; gap: 6px; font-size: 14px; color: rgba(255,255,255,0.9); margin: 0 0 12px; }
.user-meta { display: flex; gap: 8px; margin-bottom: 16px; }
.user-dates { display: flex; gap: 24px; font-size: 13px; color: rgba(255,255,255,0.75); }

/* ===== 通用区块标题 ===== */
.section-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 18px; font-weight: 600; color: var(--color-primary);
  margin: 32px 0 16px;
}
.title-icon { color: var(--color-gold); }

/* ===== 使用统计卡片 ===== */
.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
}
.stat-card {
  background: #fff; border-radius: 10px; padding: 24px 16px;
  text-align: center; box-shadow: var(--shadow-card);
  border-top: 3px solid var(--card-color);
  transition: transform 0.2s;
}
.stat-card:hover { transform: translateY(-4px); }
.stat-icon { color: var(--card-color); margin-bottom: 8px; }
.stat-value { font-size: 32px; font-weight: 700; color: var(--card-color); line-height: 1.2; }
.stat-label { font-size: 13px; color: var(--color-text-secondary); margin-top: 4px; }

.contract-extra { margin-top: 16px; }

/* ===== 活跃趋势柱状图 ===== */
.activity-chart {
  margin-top: 24px; background: #fff; border-radius: 10px; padding: 20px;
  box-shadow: var(--shadow-card);
}
.chart-title { font-size: 15px; font-weight: 600; color: var(--color-text-main); margin: 0 0 16px; }
.chart-bars { display: flex; gap: 12px; height: 200px; align-items: flex-end; }
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; }
.bar-track { width: 100%; height: 160px; display: flex; align-items: flex-end; justify-content: center; }
.bar-fill {
  width: 60%; min-height: 4px;
  background: linear-gradient(180deg, var(--color-gold), var(--color-primary));
  border-radius: 4px 4px 0 0;
  display: flex; align-items: flex-start; justify-content: center;
  transition: height 0.4s ease;
  cursor: pointer; position: relative;
}
.bar-fill:hover { filter: brightness(1.1); }
.bar-value { font-size: 11px; color: #fff; font-weight: 600; padding-top: 2px; }
.bar-label { margin-top: 8px; text-align: center; }
.bar-weekday { display: block; font-size: 12px; color: var(--color-text-secondary); }
.bar-date { display: block; font-size: 11px; color: #b8c0cb; }
.chart-tip { font-size: 12px; color: var(--color-text-secondary); text-align: center; margin: 12px 0 0; }

/* ===== 表单区 ===== */
.form-section {
  background: #fff; border-radius: 10px; padding: 24px;
  box-shadow: var(--shadow-card); margin-top: 24px;
}
.profile-form, .pwd-form { max-width: 520px; }
.form-section :deep(.el-button--primary) {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-light);
  --el-button-hover-border-color: var(--color-primary-light);
}

@media (max-width: 768px) {
  .user-card { flex-direction: column; align-items: flex-start; gap: 20px; }
  .user-left { align-self: center; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-bars { gap: 6px; }
  .bar-fill { width: 80%; }
}
</style>
