// vite.config.js —— Vite 构建工具配置文件
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],

  server: {
    host: 'localhost',
    port: 5173,
    open: false,
    // 将 /api 开头的请求代理到后端 FastAPI（8000 端口）
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },

  resolve: {
    alias: {
      '@': '/src'
    }
  }
})
