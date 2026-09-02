import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { resolve } from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    base: './',
    plugins: [
      vue(),
      Components({
        resolvers: [
          ElementPlusResolver({
            importStyle: 'css'
          })
        ],
        dts: 'src/components.d.ts'
      })
    ],
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
        },
        '/uploads': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true
        }
      }
    },
    optimizeDeps: {
      include: ['vue', 'vue-router', 'pinia', 'axios', 'element-plus']
    },
    test: {
      environment: 'jsdom', // jsdom: 与 dompurify 3.4.13+ 完全兼容；happy-dom 20 会破坏其 sanitize 行为,
      globals: true,
      include: ['src/**/*.test.js']
    },
    build: {
      chunkSizeWarningLimit: 800,
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true,
          drop_debugger: true
        }
      },
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
