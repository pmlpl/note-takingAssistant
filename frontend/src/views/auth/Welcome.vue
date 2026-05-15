<template>
  <div class="welcome-container">
    <div class="welcome-header">
      <IconNotebook :size="64" color="#409eff" />
      <h1>智能笔记助手</h1>
      <p>让AI帮你生成、总结和整理笔记，提升学习和工作效率</p>
      <div class="welcome-buttons">
        <el-button type="primary" size="large" @click="navigate('/login')">
          立即登录
        </el-button>
        <el-button size="large" @click="navigate('/register')">
          免费注册
        </el-button>
      </div>
    </div>
    
    <div class="features-section">
      <div class="feature-card">
        <IconMagic :size="48" color="#409eff" />
        <h3>智能生成</h3>
        <p>输入主题和关键词，AI自动生成专业笔记</p>
      </div>
      <div class="feature-card">
        <IconTrend :size="48" color="#67c23a" />
        <h3>智能总结</h3>
        <p>一键总结笔记内容，提取核心要点</p>
      </div>
      <div class="feature-card">
        <IconDocument :size="48" color="#f5a623" />
        <h3>笔记管理</h3>
        <p>分类整理、标签管理，轻松查找笔记</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { IconNotebook, IconMagic, IconTrend, IconDocument } from '@/components/icons'

const router = useRouter()

function navigate(path) {
  router.push(path)
}
</script>

<style scoped>
.welcome-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
  position: relative;
  overflow: hidden;
  padding: 40px 20px;
}

.welcome-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(78, 205, 196, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 40% 20%, rgba(69, 183, 209, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.welcome-header {
  text-align: center;
  color: white;
  margin-bottom: 60px;
  padding-top: 40px;
}

.welcome-header h1 {
  font-size: 48px;
  margin: 20px 0 15px 0;
  font-weight: 600;
}

.welcome-header p {
  font-size: 20px;
  margin-bottom: 40px;
  opacity: 0.95;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.welcome-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.features-section {
  display: flex;
  gap: 25px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  justify-content: center;
}

.feature-card {
  flex: 1;
  max-width: 350px;
  text-align: center;
  padding: 35px 25px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(10px);
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 1);
}

.feature-card h3 {
  margin: 20px 0 12px 0;
  font-size: 20px;
  color: #303133;
  font-weight: 600;
}

.feature-card p {
  color: #606266;
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .welcome-header h1 {
    font-size: 36px;
  }
  
  .welcome-header p {
    font-size: 16px;
  }
  
  .features-section {
    flex-direction: column;
    gap: 20px;
  }
  
  .feature-card {
    max-width: 100%;
  }
}
</style>
