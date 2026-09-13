<!-- HomePage.vue —— 首页 -->
<!-- 整体结构：英雄区（大标题 + 副标题 + CTA 搜索）→ 功能卡片区（三张卡片） -->
<script setup>
/**
 * 首页组件
 *
 * 页面结构（从上到下）：
 * 1. 英雄区（Hero）：大标题"您的智能法律助手" + 副标题 + 搜索框样式 CTA 按钮
 * 2. 功能卡片区：三张 FeatureCard 横向排列（AI法律咨询 / 文书生成 / 合同审查）
 *
 * 视觉风格：深蓝色主色调 + 金色点缀，专业、简洁、有法律感
 */

// 引入功能卡片组件
import FeatureCard from '@/components/FeatureCard.vue'
// 引入路由实例，用于 CTA 区域搜索框的跳转
import { useRouter } from 'vue-router'

const router = useRouter()

// ======== 功能模块数据 ========
// 将三张卡片的数据抽离成数组，通过 v-for 循环渲染，避免模板重复
// 好处：新增/修改模块只需改数据，不需改模板
const features = [
  {
    title: 'AI法律咨询',
    description: '智能问答，快速获取法律建议',
    // ChatDotRound：对话气泡图标，贴合"咨询"语义
    icon: 'ChatDotRound',
    to: '/ai-consult'
  },
  {
    title: '文书生成',
    description: '一键生成标准法律文书',
    // Document：文档图标，贴合"文书"语义
    icon: 'Document',
    to: '/doc-generate'
  },
  {
    title: '合同审查',
    description: '智能识别合同风险条款',
    // View：放大镜图标，贴合"审查"语义
    icon: 'View',
    to: '/contract-review'
  }
]

// ======== 搜索框 CTA 交互 ========

// 搜索框输入内容：双向绑定
import { ref } from 'vue'
const searchQuery = ref('')

/**
 * 处理搜索框回车或点击搜索按钮
 * 当前阶段为占位实现：直接跳转至 AI法律咨询页面
 * 后续可对接真实搜索接口
 */
function handleSearch() {
  router.push('/ai-consult')
}
</script>

<template>
  <div class="home">
    <!-- ============================================================
         英雄区（Hero Section）
         深蓝渐变背景 + 居中大标题 + 搜索框 CTA
         ============================================================ -->
    <section class="hero">
      <!-- 内容容器：限制宽度、垂直居中 -->
      <div class="hero-content">
        <!-- 主标题 -->
        <h1 class="hero-title">您的智能法律助手</h1>
        <!-- 金色装饰横线：标题下方点缀 -->
        <div class="hero-line"></div>
        <!-- 副标题 -->
        <p class="hero-subtitle">让法律服务触手可及</p>

        <!-- 搜索框样式 CTA 按钮 -->
        <!-- 实现为输入框 + 按钮组合，外观类似搜索框 -->
        <div class="hero-search">
          <el-input
            v-model="searchQuery"
            placeholder="输入您的法律问题，或点击直接咨询"
            size="large"
            class="hero-search-input"
            @keyup.enter="handleSearch"
          >
            <!-- 输入框前置图标 -->
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button
            type="primary"
            size="large"
            class="hero-search-btn"
            @click="handleSearch"
          >
            立即咨询
          </el-button>
        </div>
      </div>
    </section>

    <!-- ============================================================
         功能卡片区（Features Section）
         三张 FeatureCard 横向排列，展示三大核心功能
         ============================================================ -->
    <section class="features">
      <div class="page-container">
        <!-- 区块标题 -->
        <h2 class="features-title">核心功能</h2>
        <div class="gold-divider"></div>

        <!-- 卡片列表：v-for 循环渲染 -->
        <!-- :key：使用 title 作为唯一标识，保证列表渲染性能 -->
        <div class="features-grid">
          <FeatureCard
            v-for="item in features"
            :key="item.title"
            :title="item.title"
            :description="item.description"
            :icon="item.icon"
            :to="item.to"
          />
        </div>
      </div>
    </section>
  </div>
</template>

<script>
// 导出组件名，便于 Vue DevTools 识别调试
export default {
  name: 'HomePage'
}
</script>

<style scoped>
/* ======== 英雄区（Hero） ======== */
.hero {
  /* 深蓝渐变背景：上深下浅，营造稳重专业的氛围 */
  background: linear-gradient(135deg, var(--color-primary-dark) 0%, var(--color-primary) 50%, var(--color-primary-light) 100%);
  /* 高度占满首屏视口（扣除顶部导航栏高度） */
  min-height: 520px;
  padding: 80px 20px 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 底部圆角过渡到下方白色卡片区 */
  border-radius: 0 0 24px 24px;
  /* 确保层级在底部装饰元素之下 */
  position: relative;
  overflow: hidden;
}

/* 英雄区右上角金色装饰圆环（呼应点缀色） */
.hero::before {
  content: '';
  position: absolute;
  top: -60px;
  right: -60px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  border: 2px solid rgba(201, 169, 110, 0.15);
}

/* 英雄区左下角金色装饰圆环 */
.hero::after {
  content: '';
  position: absolute;
  bottom: -40px;
  left: -40px;
  width: 160px;
  height: 160px;
  border-radius: 50%;
  border: 2px solid rgba(201, 169, 110, 0.1);
}

/* 英雄区内容容器 */
.hero-content {
  text-align: center;
  max-width: 700px;
  /* 确保内容在装饰元素之上 */
  position: relative;
  z-index: 1;
}

/* 主标题：白色大字，字间距增加庄重感 */
.hero-title {
  font-size: 44px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 4px;
}

/* 金色装饰横线 */
.hero-line {
  width: 80px;
  height: 4px;
  margin: 20px auto;
  background: linear-gradient(90deg, transparent, var(--color-gold), transparent);
  border-radius: 2px;
}

/* 副标题：半透明白色，字号略小 */
.hero-subtitle {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 2px;
  margin-bottom: 40px;
}

/* ======== 搜索框 CTA ======== */
.hero-search {
  display: flex;
  gap: 12px;
  max-width: 560px;
  margin: 0 auto;
}

/* 输入框样式覆盖：圆角、白色底 */
.hero-search-input :deep(.el-input__wrapper) {
  border-radius: 28px 0 0 28px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

/* 搜索按钮：金色背景，呼应点缀色 */
.hero-search-btn {
  --el-button-bg-color: var(--color-gold);
  --el-button-border-color: var(--color-gold);
  --el-button-hover-bg-color: var(--color-gold-dark);
  --el-button-hover-border-color: var(--color-gold-dark);
  --el-button-text-color: #ffffff;
  border-radius: 0 28px 28px 0;
  padding: 0 32px;
  font-size: 15px;
  letter-spacing: 2px;
}

/* ======== 功能卡片区 ======== */
.features {
  padding: 70px 0 80px;
  background: var(--color-bg-page);
}

/* 区块标题 */
.features-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-primary);
  text-align: center;
  letter-spacing: 3px;
}

/* 卡片网格：三列横向排列，窄屏时自动换行为单列 */
.features-grid {
  margin-top: 50px;
  display: grid;
  /* 三列等宽布局 */
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
}

/* 响应式：平板尺寸改为两列 */
@media (max-width: 992px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 响应式：手机尺寸改为单列 */
@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
  .hero-subtitle {
    font-size: 16px;
  }
  .hero-search {
    flex-direction: column;
  }
  .hero-search-input :deep(.el-input__wrapper) {
    border-radius: 28px;
  }
  .hero-search-btn {
    border-radius: 28px;
  }
  .features-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
