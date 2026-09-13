// main.js —— 应用入口文件
// 负责创建 Vue 应用实例、注册全局插件（Element Plus、路由）并挂载到页面
import { createApp } from 'vue'

// 引入根组件
import App from './App.vue'

// 引入路由实例
import router from './router'

// 引入 Element Plus 组件库及其样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 引入 Element Plus 图标库
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 引入全局样式（含主题色变量、通用布局样式等）
import './assets/styles/global.css'

// 创建 Vue 应用实例
const app = createApp(App)

// 全局注册所有 Element Plus 图标组件
// 注册后可在任意组件模板中直接使用，例如：<el-icon><Search /></el-icon>
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册 Element Plus 插件（全局可用所有 el- 开头的组件）
app.use(ElementPlus)

// 注册 Vue Router，使 <router-view> 和 <router-link> 生效
app.use(router)

// 将应用挂载到 index.html 中 id 为 app 的 DOM 节点上
app.mount('#app')
