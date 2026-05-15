import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      port: 5174,
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true
        }
      }
    },
    test: {
      environment: 'happy-dom',
      globals: true,
      include: ['src/**/*.test.js']
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return
            if (id.includes('mermaid')) return 'vendor-mermaid'
            if (id.includes('echarts')) return 'vendor-echarts'
            if (id.includes('@element-plus/icons-vue')) return 'vendor-element-icons'
            if (id.includes('element-plus')) return 'vendor-element-plus'
            if (id.includes('marked') || id.includes('isomorphic-dompurify') || id.includes('dompurify')) {
              return 'vendor-markdown'
            }
            if (id.includes('mammoth')) return 'vendor-mammoth'
            if (id.includes('canvg')) return 'vendor-canvg'
            if (id.includes('axios')) return 'vendor-axios'
            // Keep Vue, Router, Pinia, and @vue/* in one graph to avoid duplicate runtime chunks
            if (id.includes('vue-router')) return 'vue-vendor'
            if (id.includes('pinia')) return 'vue-vendor'
            if (id.includes('@vue')) return 'vue-vendor'
            if (id.includes('/vue/') || id.includes('\\vue\\')) return 'vue-vendor'
          }
        }
      }
    }
  }
})
