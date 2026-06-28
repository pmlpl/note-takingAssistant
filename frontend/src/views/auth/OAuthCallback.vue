<template>
  <div class="oauth-callback">
    <div class="callback-box">
      <div v-if="loading" class="loading">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>处理中...</p>
      </div>
      <div v-else-if="success" class="success">
        <el-icon class="success-icon"><CircleCheck /></el-icon>
        <p>绑定成功！窗口即将关闭...</p>
      </div>
      <div v-else class="error">
        <el-icon class="error-icon"><CircleClose /></el-icon>
        <p>{{ errorMessage }}</p>
        <el-button size="small" @click="closeWindow">关闭</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'

const route = useRoute()
const loading = ref(true)
const success = ref(false)
const errorMessage = ref('')

function closeWindow() {
  if (window.opener) {
    window.opener.postMessage({ type: 'oauth-bind-result', success: success.value, error: errorMessage.value }, '*')
  }
  setTimeout(() => {
    window.close()
  }, 300)
}

onMounted(() => {
  const query = route.query
  if (query.success) {
    success.value = true
    loading.value = false
    if (window.opener) {
      window.opener.postMessage({ type: 'oauth-bind-result', success: true }, '*')
    }
    setTimeout(() => {
      window.close()
    }, 1500)
  } else {
    success.value = false
    errorMessage.value = query.error || '绑定失败'
    loading.value = false
    if (window.opener) {
      window.opener.postMessage({ type: 'oauth-bind-result', success: false, error: errorMessage.value }, '*')
    }
  }
})
</script>

<style scoped>
.oauth-callback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.callback-box {
  padding: 48px 64px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.loading-icon,
.success-icon,
.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.loading-icon {
  color: #409eff;
  animation: rotate 1s linear infinite;
}

.success-icon {
  color: #67c23a;
}

.error-icon {
  color: #f56c6c;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

p {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 16px;
}
</style>
