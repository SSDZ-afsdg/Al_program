<!-- FeatureCard.vue —— 功能卡片组件（首页三个功能模块复用） -->
<!-- 通过 props 接收标题、描述、图标，由父组件传入，实现组件复用 -->
<script setup>
/**
 * 功能卡片组件
 *
 * 使用方式（父组件模板中）：
 *   <FeatureCard
 *     title="AI法律咨询"
 *     description="智能问答，快速获取法律建议"
 *     icon="ChatDotRound"
 *     to="/ai-consult"
 *   />
 *
 * 设计要点：
 * - 组件本身不写死任何业务内容，全部由 props 驱动，保证通用性
 * - 点击"立即使用"按钮通过路由跳转到对应功能页面
 */

// 引入路由相关 API（必须在 setup 上下文中调用）
import { useRouter } from 'vue-router'

// 获取路由器实例，供按钮点击跳转使用
const router = useRouter()

// ======== Props 定义 ========
// defineProps 是 <script setup> 中的编译宏，无需 import 即可使用
const props = defineProps({
  // 功能模块名称，例如"AI法律咨询"
  title: {
    type: String,
    required: true
  },
  // 功能模块简短描述文案
  description: {
    type: String,
    required: true
  },
  // 图标名称：对应全局注册的 Element Plus 图标组件名
  // 例如 'ChatDotRound'、'Document'、'View'
  icon: {
    type: String,
    required: true
  },
  // 点击"立即使用"后跳转的路由路径
  to: {
    type: String,
    required: true
  }
})

// ======== 事件处理 ========

/**
 * 处理"立即使用"按钮点击
 * 使用编程式导航跳转到对应功能页面
 */
function handleUse() {
  // router.push：编程式导航，等同于点击 <router-link>
  router.push(props.to)
}
</script>

<template>
  <!-- 卡片根容器：白色圆角卡片，悬浮时上浮加深阴影 -->
  <div class="feature-card">
    <!-- ======== 图标区：圆形底衬 + 居中图标 ======== -->
    <div class="card-icon-wrap">
      <!-- 动态组件：根据 props.icon 动态渲染对应的 Element Plus 图标 -->
      <!-- is 值为图标组件名（全局已注册），如 ChatDotRound -->
      <el-icon class="card-icon" :size="34">
        <component :is="icon" />
      </el-icon>
    </div>

    <!-- ======== 标题：功能模块名称 ======== -->
    <h3 class="card-title">{{ title }}</h3>

    <!-- ======== 描述：一句话功能说明 ======== -->
    <p class="card-desc">{{ description }}</p>

    <!-- ======== 操作按钮："立即使用" ======== -->
    <el-button
      type="primary"
      class="card-btn"
      round
      @click="handleUse"
    >
      立即使用
      <!-- 按钮右侧箭头图标，暗示可点击跳转 -->
      <el-icon class="card-btn-icon"><ArrowRight /></el-icon>
    </el-button>
  </div>
</template>

<script>
// 导出组件名，便于 Vue DevTools 识别调试
export default {
  name: 'FeatureCard'
}
</script>

<style scoped>
/* ======== 卡片容器 ======== */
.feature-card {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: var(--shadow-card);
  padding: 40px 28px 36px;
  text-align: center;
  /* 过渡动画：悬浮时阴影与位置变化更平滑 */
  transition: all 0.3s ease;
}

/* 悬浮效果：卡片上移 + 顶部出现金色描边（法律感点缀） */
.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-card-hover);
  border-top: 3px solid var(--color-gold);
  /* 抵消顶部边框造成的 1px 抖动 */
  padding-top: 38px;
}

/* ======== 图标区 ======== */
.card-icon-wrap {
  width: 76px;
  height: 76px;
  margin: 0 auto 20px;
  border-radius: 50%;
  /* 深蓝色浅底：衬托图标 */
  background: rgba(26, 58, 92, 0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

/* 悬浮卡片时图标容器变深蓝、图标变金色，形成强对比 */
.feature-card:hover .card-icon-wrap {
  background: var(--color-primary);
}

.feature-card:hover .card-icon {
  color: var(--color-gold);
}

/* 图标默认颜色：深蓝主色调 */
.card-icon {
  color: var(--color-primary);
}

/* ======== 文字区 ======== */
.card-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 12px;
}

.card-desc {
  font-size: 14px;
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin-bottom: 24px;
  /* 限制描述文字高度一致，保证三张卡片按钮对齐 */
  min-height: 44px;
}

/* ======== 按钮 ======== */
.card-btn {
  /* 覆盖 Element Plus 主色：改为品牌深蓝 */
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-light);
  --el-button-hover-border-color: var(--color-primary-light);
  padding: 12px 28px;
  font-size: 14px;
  letter-spacing: 1px;
}

/* 按钮内箭头图标 */
.card-btn-icon {
  margin-left: 6px;
}

/* 按钮悬停时：文字图标变金色，呼应点缀色 */
.card-btn:hover .card-btn-icon {
  color: var(--color-gold);
}
</style>
