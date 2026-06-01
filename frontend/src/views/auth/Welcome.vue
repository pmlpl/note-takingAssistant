<template>
  <div class="welcome-container">
    <div class="welcome-header">
      <IconNotebook :size="72" color="var(--color-pencil)" />
      <h1>智能笔记助手</h1>
      <p>让 AI 帮你生成、总结和整理笔记<span class="wavy-underline">，提升学习和工作效率</span></p>
      <div class="welcome-buttons">
        <el-button type="primary" size="large" class="hero-btn" @click="navigate('/login')">
          立即登录
        </el-button>
        <el-button size="large" class="hero-btn-outline" @click="navigate('/register')">
          免费注册
        </el-button>
      </div>
    </div>

    <div class="features-section">
      <!-- Feature Card 1 -->
      <div class="feature-card rotate-n1">
        <div class="tape-strip"></div>
        <IconMagic :size="52" color="var(--color-pencil)" />
        <h3>智能生成</h3>
        <p>输入主题和关键词，AI 自动生成专业笔记</p>
      </div>

      <!-- Feature Card 2 -->
      <div class="feature-card rotate-p1">
        <div class="tape-strip"></div>
        <IconTrend :size="52" color="var(--color-blue)" />
        <h3>智能总结</h3>
        <p>一键总结笔记内容，提取核心要点</p>
      </div>

      <!-- Feature Card 3 — post-it yellow -->
      <div class="feature-card feature-card--yellow rotate-n2">
        <div class="tape-strip"></div>
        <IconDocument :size="52" color="var(--color-pencil)" />
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
/* ═══ Welcome Page — Hand-Drawn Theme ═══ */

.welcome-container {
  min-height: 100vh;
  background-color: var(--color-paper);
  background-image: radial-gradient(var(--color-muted) 1px, transparent 1px);
  background-size: 24px 24px;
  position: relative;
  overflow: hidden;
  padding: 40px 20px 80px;
}

/* ── Hero Section ── */
.welcome-header {
  text-align: center;
  color: var(--color-pencil);
  margin-bottom: 70px;
  padding-top: 50px;
  position: relative;
}

.welcome-header h1 {
  font-family: var(--font-heading);
  font-size: 52px;
  margin: 24px 0 16px;
  font-weight: 700;
}

.welcome-header p {
  font-size: 20px;
  margin-bottom: 44px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  font-family: var(--font-body);
  line-height: 1.7;
}

/* Wavy underline on the last phrase */
.wavy-underline {
  text-decoration: underline wavy var(--color-accent) 3px;
  text-underline-offset: 6px;
}

.welcome-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.hero-btn,
.hero-btn-outline {
  font-size: 20px !important;
  padding: 14px 36px !important;
  height: auto !important;
}

.hero-btn-outline {
  background: #fff !important;
}

/* ── Feature Cards ── */
.features-section {
  display: flex;
  gap: 30px;
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 20px;
  justify-content: center;
  flex-wrap: wrap;
}

.feature-card {
  flex: 1;
  min-width: 260px;
  max-width: 340px;
  text-align: center;
  padding: 40px 28px 30px;
  background: #ffffff;
  border: 3px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard);
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-6px) rotate(0deg) !important;
  box-shadow: 8px 8px 0px 0px var(--color-pencil);
}

/* Post-it yellow variant */
.feature-card--yellow {
  background: var(--color-yellow);
}

/* Slight rotations for casual feel */
.rotate-n1 { transform: rotate(-1deg); }
.rotate-p1 { transform: rotate(1deg); }
.rotate-n2 { transform: rotate(-2deg); }

/* Tape strip decoration */
.tape-strip {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%) rotate(-2deg);
  width: 80px;
  height: 22px;
  background: rgba(180, 180, 180, 0.4);
  border-radius: 2px;
}

.feature-card h3 {
  margin: 18px 0 10px;
  font-family: var(--font-heading);
  font-size: 22px;
  font-weight: 700;
  color: var(--color-pencil);
}

.feature-card p {
  color: #555;
  font-family: var(--font-body);
  margin: 0;
  font-size: 16px;
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
    align-items: center;
    gap: 24px;
  }
  .feature-card {
    max-width: 100%;
    transform: rotate(0) !important;
  }
}
</style>
