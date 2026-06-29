<template>
  <div class="welcome-landing">
    <!-- 顶栏 -->
    <header
      class="welcome-nav"
      :class="{ 'welcome-nav--scrolled': navScrolled, 'welcome-nav--transparent': !navScrolled }"
    >
      <div class="nav-inner">
        <div class="nav-brand" @click="scrollToTop">
          <AppLogo :size="32" />
          <span>智能笔记助手</span>
        </div>
        <nav class="nav-links">
          <a
            class="nav-link-github"
            :href="GITHUB_REPO_URL"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub 开源仓库"
            title="GitHub"
          >
            <IconGitHub :size="22" color="currentColor" />
          </a>
          <el-button link class="nav-btn-link" @click="navigate('/login')">登录</el-button>
          <el-button type="primary" class="nav-btn-primary" @click="navigate('/register')">
            免费注册
          </el-button>
        </nav>
      </div>
    </header>

    <!-- Hero 首屏 -->
    <section class="hero-banner">
      <div class="hero-particles" aria-hidden="true">
        <span v-for="n in 6" :key="n" class="particle" :class="`particle--${n}`" />
      </div>
      <img
        class="hero-banner__img"
        src="/welcome/welcome-hero-banner.png"
        alt=""
        fetchpriority="high"
        decoding="async"
      />
      <div class="hero-banner__scrim" aria-hidden="true" />
      <div class="hero-banner__content">
        <div class="hero-badge">
          <span class="badge-dot" />
          基于 Vue 3 + FastAPI 构建
        </div>
        <h1>
          让 AI 成为你的
          <span class="wavy">学习搭档</span>
        </h1>
        <p class="hero-lead">
          智能笔记助手帮你写笔记、做总结、画导图，支持接入本地 LM Studio，数据完全自主可控。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="navigate('/register')">
            免费开始使用
          </el-button>
          <el-button size="large" class="hero-outline" @click="navigate('/login')">
            已有账号登录
          </el-button>
        </div>
        <div class="hero-tech-strip">
          <span v-for="tech in TECH_HIGHLIGHTS" :key="tech.label" class="tech-chip">
            {{ tech.label }}
          </span>
        </div>
      </div>
      <div class="hero-scroll-hint" aria-hidden="true">
        <span class="scroll-arrow" />
      </div>
    </section>

    <!-- 下方内容 -->
    <div class="landing-flow">
      <!-- 核心功能 -->
      <section id="features" ref="featuresAnchor" class="features-section">
        <header class="section-header">
          <span class="section-eyebrow">CORE FEATURES</span>
          <h2>四大核心能力</h2>
          <p>从笔记生成到知识可视化，AI 全程辅助你的学习</p>
        </header>
        <div class="features-grid">
          <WelcomeFeatureRow
            v-for="item in WELCOME_FEATURES"
            :key="item.id"
            :feature="item"
            @navigate="navigate"
          />
        </div>
      </section>

      <hr class="landing-divider" aria-hidden="true" />

      <!-- 使用步骤 -->
      <section id="how-it-works" ref="stepsAnchor" class="steps-section" :class="{ 'is-visible': stepsVisible }">
        <header class="section-header">
          <span class="section-eyebrow">HOW IT WORKS</span>
          <h2>四步开始使用</h2>
          <p>简单几步，立即体验 AI 驱动的智能笔记</p>
        </header>
        <div class="steps-grid">
          <div
            v-for="item in HOW_IT_WORKS"
            :key="item.step"
            class="step-card"
            :style="{ '--step-delay': `${(item.step - 1) * 0.12}s` }"
          >
            <div class="step-number">{{ item.step }}</div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
            <div class="step-connector" aria-hidden="true" v-if="item.step < HOW_IT_WORKS.length" />
          </div>
        </div>
      </section>

      <hr class="landing-divider" aria-hidden="true" />

      <!-- 平台数据 -->
      <div id="stats" ref="statsAnchor" class="landing-flow__panel">
        <WelcomeStatsBlock />
      </div>

      <!-- CTA 底部号召 -->
      <section ref="ctaRoot" class="cta-section" :class="{ 'is-visible': ctaVisible }">
        <div class="cta-inner">
          <h2>准备好提升学习效率了吗？</h2>
          <p>注册即可免费使用全部 AI 功能，无需付费</p>
          <div class="cta-actions">
            <el-button type="primary" size="large" @click="navigate('/register')">
              立即免费注册
            </el-button>
            <a
              class="cta-github"
              :href="GITHUB_REPO_URL"
              target="_blank"
              rel="noopener noreferrer"
            >
              <IconGitHub :size="20" color="currentColor" />
              <span>查看开源仓库</span>
            </a>
          </div>
        </div>
      </section>
    </div>

    <SiteFooter @navigate="navigate" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { AppLogo, IconGitHub } from '@/components/icons'
import WelcomeStatsBlock from '@/components/welcome/WelcomeStatsBlock.vue'
import WelcomeFeatureRow from '@/components/welcome/WelcomeFeatureRow.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import { useLazyReveal } from '@/composables/useLazyReveal'
import {
  WELCOME_FEATURES,
  GITHUB_REPO_URL,
  HOW_IT_WORKS,
  TECH_HIGHLIGHTS,
} from '@/constants/welcomeLanding'

const router = useRouter()
const navScrolled = ref(false)
const statsAnchor = ref(null)

const { root: stepsAnchor, visible: stepsVisible } = useLazyReveal()
const { root: ctaRoot, visible: ctaVisible } = useLazyReveal()

function navigate(path) {
  router.push(path)
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onWindowScroll() {
  navScrolled.value = window.scrollY > 24
}

onMounted(() => {
  window.addEventListener('scroll', onWindowScroll, { passive: true })
  onWindowScroll()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onWindowScroll)
})
</script>

<style scoped>
.welcome-landing {
  --landing-paper: #f7f2e8;
  --landing-paper-dot: #ddd6c8;
  width: 100%;
  max-width: 100vw;
  min-height: 100vh;
  overflow-x: hidden;
  background-color: var(--landing-paper);
  background-image: radial-gradient(var(--landing-paper-dot) 1px, transparent 1px);
  background-size: 24px 24px;
  color: var(--color-pencil);
}

/* ── 通用分隔线 ── */
.landing-divider {
  display: block;
  width: min(80px, 12vw);
  margin: 16px auto;
  border: none;
  border-top: 3px solid var(--color-pencil);
  height: 0;
  opacity: 0.25;
}

/* ── 通用区块标题 ── */
.section-header {
  text-align: center;
  padding: 48px clamp(16px, 3vw, 40px) 32px;
  max-width: 640px;
  margin: 0 auto;
}

.section-eyebrow {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--color-blue);
  background: rgba(45, 93, 161, 0.08);
  padding: 4px 14px;
  border-radius: 20px;
  border: 1.5px solid rgba(45, 93, 161, 0.2);
  margin-bottom: 16px;
}

.section-header h2 {
  font-family: var(--font-heading);
  font-size: clamp(28px, 4vw, 40px);
  margin: 0 0 12px;
  line-height: 1.2;
}

.section-header p {
  margin: 0;
  color: #666;
  font-size: clamp(15px, 1.6vw, 17px);
  line-height: 1.7;
}

/* ── 顶栏 ── */
.welcome-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  transition: background 0.3s ease, box-shadow 0.3s ease;
}

.welcome-nav--transparent {
  background: transparent;
  box-shadow: none;
}

.welcome-nav--scrolled {
  background: rgba(247, 242, 232, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 2px 16px rgba(45, 45, 45, 0.06);
}

.nav-inner {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 14px clamp(20px, 4vw, 40px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 700;
  transition: opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.8;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.nav-link-github {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  color: var(--color-pencil);
  text-decoration: none;
  border: 2px solid rgba(45, 45, 45, 0.15);
  border-radius: var(--radius-wobbly-sm);
  background: rgba(255, 255, 255, 0.5);
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.nav-link-github:hover {
  background: var(--color-yellow);
  border-color: var(--color-pencil);
  transform: translateY(-2px);
}

.welcome-nav--scrolled .nav-link-github {
  background: #faf9f6;
  border-color: rgba(45, 45, 45, 0.25);
}

.nav-btn-link {
  font-size: 15px !important;
}

.nav-btn-primary {
  font-size: 15px !important;
}

/* ── Hero 首屏 ── */
.hero-banner {
  position: relative;
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  margin-top: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
}

/* Hero 底部渐隐 */
.hero-banner::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: min(32vh, 240px);
  z-index: 2;
  pointer-events: none;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(247, 242, 232, 0.55) 45%,
    var(--landing-paper) 100%
  );
}

/* 浮动粒子装饰 */
.hero-particles {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  display: block;
  border-radius: 50%;
  opacity: 0.12;
}

.particle--1 {
  width: 120px; height: 120px;
  background: var(--color-yellow);
  top: 15%; right: 8%;
  animation: particleFloat 8s ease-in-out infinite;
}
.particle--2 {
  width: 80px; height: 80px;
  background: var(--color-blue);
  top: 60%; right: 15%;
  animation: particleFloat 6s ease-in-out 1s infinite;
}
.particle--3 {
  width: 60px; height: 60px;
  background: var(--color-accent);
  top: 30%; right: 35%;
  animation: particleFloat 10s ease-in-out 2s infinite;
}
.particle--4 {
  width: 40px; height: 40px;
  background: var(--color-yellow);
  bottom: 25%; left: 60%;
  animation: particleFloat 7s ease-in-out 0.5s infinite;
}
.particle--5 {
  width: 90px; height: 90px;
  background: var(--color-blue);
  bottom: 30%; right: 25%;
  opacity: 0.08;
  animation: particleFloat 12s ease-in-out 3s infinite;
}
.particle--6 {
  width: 50px; height: 50px;
  background: var(--color-accent);
  top: 20%; right: 50%;
  opacity: 0.06;
  animation: particleFloat 9s ease-in-out 1.5s infinite;
}

@keyframes particleFloat {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  33% { transform: translateY(-20px) rotate(5deg); }
  66% { transform: translateY(10px) rotate(-3deg); }
}

.hero-banner__img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: 72% center;
  display: block;
}

.hero-banner__scrim {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(
    100deg,
    rgba(247, 242, 232, 0.97) 0%,
    rgba(247, 242, 232, 0.92) 35%,
    rgba(247, 242, 232, 0.4) 55%,
    rgba(247, 242, 232, 0.1) 68%
  );
  pointer-events: none;
}

.hero-banner__content {
  position: relative;
  z-index: 3;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: calc(80px + env(safe-area-inset-top, 0px)) clamp(24px, 5vw, 48px) 80px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  flex: 1;
}

.hero-banner__content h1,
.hero-banner__content .hero-lead,
.hero-banner__content .hero-actions {
  max-width: 580px;
}

/* 技术徽章 */
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--color-blue);
  background: rgba(45, 93, 161, 0.06);
  border: 1.5px solid rgba(45, 93, 161, 0.18);
  border-radius: 24px;
  margin-bottom: 24px;
  letter-spacing: 0.02em;
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4caf50;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.hero-banner__content h1 {
  font-family: var(--font-heading);
  font-size: clamp(32px, 5vw, 56px);
  line-height: 1.18;
  margin: 0 0 20px;
  color: var(--color-pencil);
}

.wavy {
  color: var(--color-accent);
  text-decoration: underline wavy var(--color-accent) 3px;
  text-underline-offset: 6px;
  text-decoration-skip-ink: none;
}

.hero-lead {
  font-size: clamp(15px, 2vw, 18px);
  line-height: 1.8;
  color: #3a3a3a;
  margin: 0 0 32px;
  max-width: 520px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 28px;
}

.hero-outline {
  background: rgba(255, 255, 255, 0.92) !important;
}

/* 技术栈标签条 */
.hero-tech-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tech-chip {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 4px 12px;
  border: 1.5px solid rgba(45, 45, 45, 0.15);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.6);
  color: #555;
  backdrop-filter: blur(4px);
}

/* 滚动提示 */
.hero-scroll-hint {
  position: absolute;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 3;
  opacity: 0.5;
  animation: scrollBounce 2s ease-in-out infinite;
}

.scroll-arrow {
  display: block;
  width: 24px;
  height: 24px;
  border-right: 2.5px solid var(--color-pencil);
  border-bottom: 2.5px solid var(--color-pencil);
  transform: rotate(45deg);
}

@keyframes scrollBounce {
  0%, 100% { transform: translateX(-50%) translateY(0); opacity: 0.5; }
  50% { transform: translateX(-50%) translateY(8px); opacity: 0.8; }
}

/* ── 内容区 ── */
.landing-flow {
  position: relative;
  z-index: 5;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 clamp(20px, 4vw, 48px) 24px;
}

.landing-flow__panel {
  margin-bottom: 16px;
  padding-top: 8px;
}

#stats,
#features,
#how-it-works {
  scroll-margin-top: 72px;
}

/* ── 功能网格 ── */
.features-section {
  padding: 24px 0 16px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

/* ── 使用步骤 ── */
.steps-section {
  width: 100%;
  padding: 24px 0 16px;
  opacity: 0;
  transform: translateY(32px);
  transition: opacity 0.7s ease, transform 0.7s ease;
}

.steps-section.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  position: relative;
}

.step-card {
  position: relative;
  text-align: center;
  padding: 32px 20px 24px;
  background: rgba(255, 255, 255, 0.65);
  border: 2.5px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard-sm);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  opacity: 0;
  transform: translateY(20px);
  animation: stepFadeIn 0.5s ease forwards;
  animation-delay: var(--step-delay);
}

@keyframes stepFadeIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.step-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hard);
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  font-family: var(--font-heading);
  font-size: 24px;
  font-weight: 700;
  color: var(--color-accent);
  border: 3px solid var(--color-accent);
  border-radius: 50%;
  margin-bottom: 16px;
  background: rgba(255, 77, 77, 0.06);
}

.step-card h3 {
  font-family: var(--font-heading);
  font-size: 20px;
  margin: 0 0 10px;
}

.step-card p {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin: 0;
}

/* 步骤间的连接线 */
.step-connector {
  display: none;
}

/* ── CTA 底部号召 ── */
.cta-section {
  width: 100%;
  padding: 48px 0 64px;
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.65s ease, transform 0.65s ease;
}

.cta-section.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.cta-inner {
  text-align: center;
  padding: 48px clamp(24px, 5vw, 48px);
  background: var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  color: #f5f0e6;
  position: relative;
  overflow: hidden;
}

.cta-inner::before {
  content: '';
  position: absolute;
  top: -40px;
  right: -40px;
  width: 160px;
  height: 160px;
  background: var(--color-accent);
  border-radius: 50%;
  opacity: 0.15;
}

.cta-inner::after {
  content: '';
  position: absolute;
  bottom: -30px;
  left: -30px;
  width: 120px;
  height: 120px;
  background: var(--color-blue);
  border-radius: 50%;
  opacity: 0.15;
}

.cta-inner h2 {
  font-family: var(--font-heading);
  font-size: clamp(24px, 3.5vw, 36px);
  color: #fff;
  margin: 0 0 12px;
  position: relative;
  z-index: 1;
}

.cta-inner p {
  color: rgba(245, 240, 230, 0.7);
  font-size: 16px;
  margin: 0 0 28px;
  position: relative;
  z-index: 1;
}

.cta-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}

.cta-actions .el-button--primary {
  background: var(--color-accent) !important;
  border-color: var(--color-accent) !important;
  font-size: 17px !important;
}

.cta-actions .el-button--primary:hover {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px 0px 0px rgba(255, 77, 77, 0.4) !important;
}

.cta-github {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: rgba(245, 240, 230, 0.8);
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
  padding: 8px 20px;
  border: 2px solid rgba(245, 240, 230, 0.3);
  border-radius: var(--radius-wobbly-sm);
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}

.cta-github:hover {
  color: #fff;
  border-color: rgba(245, 240, 230, 0.6);
  background: rgba(255, 255, 255, 0.08);
}

/* ── 响应式 ── */
@media (max-width: 900px) {
  .hero-banner {
    min-height: 100vh;
    min-height: 100dvh;
    min-height: 100svh;
    flex-direction: column;
    align-items: stretch;
  }

  .hero-banner__img {
    object-position: 65% center;
  }

  .hero-banner__scrim {
    background: linear-gradient(
      180deg,
      rgba(247, 242, 232, 0.96) 0%,
      rgba(247, 242, 232, 0.88) 55%,
      rgba(247, 242, 232, 0.5) 100%
    );
  }

  .hero-banner__content {
    max-width: 100%;
    padding: calc(72px + env(safe-area-inset-top, 0px)) 20px 60px;
    justify-content: center;
    flex: 1;
    box-sizing: border-box;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .steps-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .landing-flow {
    padding: 0 16px 20px;
  }
}

@media (max-width: 520px) {
  .hero-banner__content h1 {
    font-size: 28px;
  }

  .hero-tech-strip {
    display: none;
  }

  .steps-grid {
    grid-template-columns: 1fr;
  }

  .cta-inner {
    padding: 36px 20px;
  }
}
</style>
