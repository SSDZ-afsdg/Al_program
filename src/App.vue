<!-- App.vue —— 应用根组件 -->
<!-- 所有页面都将渲染在该组件的 <router-view> 中，负责整体页面骨架布局 -->
<script setup>
// 使用 <script setup> 语法糖，代码更简洁，变量和函数无需显式 return 即可在模板中使用

// 引入顶部导航栏与底部信息栏组件（在模板中直接使用标签 <AppHeader /> <AppFooter />）
import AppHeader from '@/components/AppHeader.vue'
import AppFooter from '@/components/AppFooter.vue'
</script>

<template>
  <!-- 应用最外层容器：纵向弹性布局，保证底部栏始终贴在页面最下方 -->
  <el-container class="app-container">
    <!-- 顶部导航栏：通用于所有页面，包含 Logo 与导航链接 -->
    <AppHeader />

    <!-- 主内容区：路由匹配到的页面组件将渲染在此处 -->
    <el-main class="app-main">
      <!-- 路由出口：根据当前 URL 渲染对应的页面组件（HomePage / AiConsult 等） -->
      <router-view />
    </el-main>

    <!-- 底部信息栏：通用于所有页面，包含版权信息与免责声明 -->
    <AppFooter />
  </el-container>
</template>

<script>
// 采用普通 script 导出组件名，便于开发调试时在 Vue DevTools 中识别组件
export default {
  name: 'App'
}
</script>

<style scoped>
/* scoped 样式：仅作用于当前组件，避免污染其他组件 */

/* 应用整体容器：最小高度占满视口，纵向排列（头部 - 主体 - 底部） */
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 主内容区：弹性伸展占据剩余空间，使底部栏在内容不足时仍位于页面底部 */
.app-main {
  flex: 1;
  /* Element Plus 的 el-main 默认有 20px 内边距，这里清除以便页面自行控制 */
  padding: 0;
  /* 覆盖默认 overflow:auto，交由各页面自己管理滚动，避免出现双滚动条 */
  overflow: visible;
}
</style>
