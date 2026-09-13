<!-- AppFooter.vue —— 底部信息栏组件（全局通用） -->
<!-- 布局：上部分为功能/品牌信息，下部分为版权信息与免责声明 -->
<script setup>
/**
 * 底部信息栏组件
 * 无需外部传参，内容为静态版权与免责声明
 */

// 当前年份：动态计算，保证版权年份始终是最新的
const currentYear = new Date().getFullYear()

// 免责声明文字：明确 AI 服务的定位边界，规避法律风险
const disclaimer =
  '法宝AI法律助手提供的所有内容由人工智能生成，仅供参考，不构成正式法律意见。' +
  '对于您的具体法律事务，请咨询执业律师或相关专业机构。'
</script>

<template>
  <!-- el-footer：Element Plus 的底部容器组件 -->
  <el-footer class="app-footer">
    <div class="footer-inner">
      <!-- ======== 上半部分：品牌标语与快捷导航 ======== -->
      <div class="footer-top">
        <!-- 左侧：品牌名与标语 -->
        <div class="footer-brand">
          <el-icon class="footer-logo" :size="28">
            <Balance />
          </el-icon>
          <div class="footer-brand-text">
            <p class="footer-name">法宝 AI法律助手</p>
            <p class="footer-slogan">让法律服务触手可及</p>
          </div>
        </div>

        <!-- 右侧：快捷导航链接（与顶部导航一致，方便页尾快速跳转） -->
        <nav class="footer-nav">
          <router-link to="/ai-consult" class="footer-link">AI法律咨询</router-link>
          <router-link to="/doc-generate" class="footer-link">文书生成</router-link>
          <router-link to="/contract-review" class="footer-link">合同审查</router-link>
        </nav>
      </div>

      <!-- ======== 分割线 ======== -->
      <el-divider class="footer-divider" />

      <!-- ======== 下半部分：版权信息与免责声明 ======== -->
      <div class="footer-bottom">
        <!-- 版权信息：年份动态生成 -->
        <p class="copyright">© {{ currentYear }} 法宝AI法律助手 · 保留所有权利</p>
        <!-- 免责声明：小号灰色文字，明确 AI 内容仅供参考 -->
        <p class="disclaimer">{{ disclaimer }}</p>
      </div>
    </div>
  </el-footer>
</template>

<script>
// 导出组件名，便于 Vue DevTools 识别调试
export default {
  name: 'AppFooter'
}
</script>

<style scoped>
/* ======== 底部整体样式 ======== */
.app-footer {
  /* 深蓝色背景与顶部导航呼应，形成头尾包裹的视觉框架 */
  background: var(--color-primary);
  color: rgba(255, 255, 255, 0.75);
  /* 调整 el-footer 默认高度，容纳更多内容 */
  height: auto;
  padding: 40px 0 24px;
}

/* 内部容器：与页面主体同宽对齐 */
.footer-inner {
  max-width: var(--container-width);
  margin: 0 auto;
  padding: 0 20px;
}

/* ======== 上半部分：品牌区 + 导航区 ======== */
.footer-top {
  display: flex;
  justify-content: space-between; /* 左右分布 */
  align-items: flex-start;
  flex-wrap: wrap; /* 窄屏时允许换行 */
  gap: 24px;
}

/* 品牌区：图标 + 文字横向排列 */
.footer-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 页脚 Logo 图标：金色点缀 */
.footer-logo {
  color: var(--color-gold);
}

/* 品牌名称：白色加粗 */
.footer-name {
  font-size: 17px;
  font-weight: 600;
  color: #ffffff;
}

/* 品牌标语：小号半透明文字 */
.footer-slogan {
  margin-top: 4px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}

/* 快捷导航区：链接横向排列 */
.footer-nav {
  display: flex;
  gap: 28px;
}

/* 页脚导航链接样式 */
.footer-link {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  transition: color 0.25s ease;
}

/* 悬停时变金色 */
.footer-link:hover {
  color: var(--color-gold);
}

/* ======== 分割线 ======== */
.footer-divider {
  /* 覆盖 Element Plus 默认颜色，改为半透明白色细线 */
  border-color: rgba(255, 255, 255, 0.15);
  margin: 24px 0 16px;
}

/* ======== 下半部分：版权与免责声明 ======== */
.footer-bottom {
  text-align: center;
}

/* 版权信息 */
.copyright {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

/* 免责声明：字号更小，弱化视觉但不缺席（合规要求） */
.disclaimer {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.45);
}
</style>
