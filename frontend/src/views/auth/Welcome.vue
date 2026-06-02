<template>
  <div class="welcome-landing">
    <!-- 顶栏：登录 / 注册固定在右上 -->
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

    <!-- 首屏 Hero：全宽横幅 + 文案叠在左侧留白区 -->
    <section class="hero-banner">
      <img
        class="hero-banner__img"
        src="/welcome/welcome-hero-banner.png"
        alt=""
        fetchpriority="high"
        decoding="async"
      />
      <div class="hero-banner__scrim" aria-hidden="true" />
      <div class="hero-banner__content">
        <h1>
          让 AI 帮你
          <span class="wavy">写笔记、做总结、画导图</span>
        </h1>
        <p class="hero-lead">
          基于 Vue 3 + FastAPI 的全栈智能笔记助手，支持 BYOK 接入本地 LM Studio。
          向下滚动了解更多。
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="navigate('/register')">
            免费开始使用
          </el-button>
          <el-button size="large" class="hero-outline" @click="navigate('/login')">
            已有账号登录
          </el-button>
        </div>
      </div>
    </section>

    <!-- 下方内容：与 Hero 同列宽，留出呼吸间距 -->
    <div class="landing-flow">
      <div id="stats" ref="statsAnchor" class="landing-flow__panel">
        <WelcomeStatsBlock />
      </div>

      <hr class="landing-divider" aria-hidden="true" />

      <div id="features" class="features-wrap">
        <header class="section-title">
          <h2>核心能力</h2>
          <p>滚动浏览各项功能，图文随视野逐步呈现</p>
        </header>
        <WelcomeFeatureRow
          v-for="item in WELCOME_FEATURES"
          :key="item.id"
          :feature="item"
          @navigate="navigate"
        />
      </div>

      <hr class="landing-divider" aria-hidden="true" />

      <section id="download" ref="downloadRoot" class="download-section" :class="{ 'is-visible': downloadVisible }">
      <div class="download-inner">
        <h2>客户端下载</h2>
        <p class="download-lead">桌面端与手机端正在开发，可先收藏仓库获取更新</p>
        <div class="download-cards">
          <div
            v-for="item in DOWNLOAD_PLACEHOLDERS"
            :key="item.id"
            class="download-card"
          >
            <div class="download-icon">{{ item.ext }}</div>
            <h3>{{ item.label }}</h3>
            <p>{{ item.hint }}</p>
            <el-button disabled class="download-btn">即将推出</el-button>
          </div>
        </div>
        <a
          class="repo-link"
          :href="GITHUB_REPO_URL"
          target="_blank"
          rel="noopener noreferrer"
        >
          开源仓库：pmlpl/note-takingAssistant →
        </a>
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
  DOWNLOAD_PLACEHOLDERS,
} from '@/constants/welcomeLanding'

const router = useRouter()
const navScrolled = ref(false)
const statsAnchor = ref(null)

const { root: downloadRoot, visible: downloadVisible } = useLazyReveal()

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

.landing-divider {
  display: block;
  width: min(260px, 36vw);
  margin: 28px auto;
  border: none;
  border-top: 2px dashed rgba(45, 45, 45, 0.38);
  height: 0;
}

/* ── 顶栏 ── */
.welcome-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  transition: background 0.25s ease, box-shadow 0.25s ease;
}

.welcome-nav--transparent {
  background: transparent;
  box-shadow: none;
}

.welcome-nav--scrolled {
  background: rgba(247, 242, 232, 0.94);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 0 var(--color-muted);
}

.nav-inner {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 12px clamp(16px, 3vw, 40px);
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
  border: 2px solid rgba(45, 45, 45, 0.2);
  border-radius: var(--radius-wobbly-sm);
  background: rgba(255, 255, 255, 0.5);
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.nav-link-github:hover {
  background: var(--color-yellow);
  border-color: var(--color-pencil);
  transform: translateY(-1px);
}

.welcome-nav--scrolled .nav-link-github {
  background: #faf9f6;
  border-color: rgba(45, 45, 45, 0.35);
}

.nav-btn-link {
  font-size: 15px !important;
}

.nav-btn-primary {
  font-size: 15px !important;
}

/* ── Hero 全宽横幅：占满首屏，下拉后才见下方内容 ── */
.hero-banner {
  position: relative;
  width: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  min-height: 100svh;
  margin-top: 0;
  overflow: hidden;
  border-bottom: none;
  box-sizing: border-box;
  display: flex;
  align-items: center;
}

/* Hero 底部渐隐到纸纹背景，取代生硬虚线分割 */
.hero-banner::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: min(28vh, 200px);
  z-index: 2;
  pointer-events: none;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(247, 242, 232, 0.55) 45%,
    var(--landing-paper) 100%
  );
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
    rgba(247, 242, 232, 0.88) 38%,
    rgba(247, 242, 232, 0.35) 58%,
    transparent 72%
  );
  pointer-events: none;
}

.hero-banner__content {
  position: relative;
  z-index: 3;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: calc(72px + env(safe-area-inset-top, 0px)) clamp(20px, 4vw, 40px) 56px;
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
  max-width: 560px;
}

.hero-banner__content h1 {
  font-family: var(--font-heading);
  font-size: clamp(30px, 4.8vw, 52px);
  line-height: 1.22;
  margin: 0 0 20px;
  color: var(--color-pencil);
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.8);
}

.wavy {
  text-decoration: underline wavy var(--color-accent) 3px;
  text-underline-offset: 6px;
}

.hero-lead {
  font-size: clamp(15px, 2vw, 18px);
  line-height: 1.75;
  color: #3a3a3a;
  margin: 0 0 28px;
  max-width: 520px;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hero-outline {
  background: rgba(255, 255, 255, 0.92) !important;
}

/* 与 Hero 衔接的内容区：统一列宽、轻微上浮叠层 */
.landing-flow {
  position: relative;
  z-index: 5;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 80px 0 24px;
}

.landing-flow__panel {
  margin-bottom: 16px;
  padding-top: 8px;
}

#stats,
#features,
#download {
  scroll-margin-top: 72px;
}

.landing-flow__eyebrow {
  text-align: center;
  margin: 0 0 12px;
  padding: 0 clamp(16px, 3vw, 40px);
  font-family: var(--font-heading);
  font-size: 15px;
  letter-spacing: 0.12em;
  color: #888;
  text-transform: uppercase;
}

.features-wrap {
  width: 100%;
  padding-bottom: 0;
}

.section-title {
  text-align: center;
  padding: 40px clamp(16px, 3vw, 40px) 16px;
  max-width: none;
  margin: 0;
}

.section-title h2 {
  font-family: var(--font-heading);
  font-size: 32px;
  margin: 0 0 8px;
}

.section-title p {
  margin: 0;
  color: #666;
}

/* ── 下载区 ── */
.download-section {
  width: 100%;
  padding: 56px 0 72px;
  box-sizing: border-box;
  opacity: 0;
  transform: translateY(32px);
  transition: opacity 0.65s ease, transform 0.65s ease;
}

.download-section.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.download-inner {
  width: min(1100px, calc(100% - clamp(32px, 6vw, 80px)));
  max-width: 1100px;
  margin: 0 auto;
  text-align: center;
  background: rgba(255, 255, 255, 0.72);
  border: 3px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard);
  padding: 40px clamp(20px, 4vw, 40px);
  box-sizing: border-box;
}

.download-inner h2 {
  font-family: var(--font-heading);
  font-size: 28px;
  margin: 0 0 8px;
}

.download-lead {
  color: #666;
  margin: 0 0 28px;
}

.download-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.download-card {
  padding: 24px 16px;
  border: 2px dashed var(--color-muted);
  border-radius: var(--radius-wobbly-sm);
  background: #faf9f6;
}

.download-icon {
  font-family: var(--font-mono);
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--color-blue);
}

.download-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.download-card p {
  margin: 0 0 16px;
  font-size: 14px;
  color: #777;
}

.download-btn {
  width: 100%;
}

.repo-link {
  color: var(--color-blue);
  font-weight: 600;
  text-decoration: none;
}

.repo-link:hover {
  text-decoration: underline;
}

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
      rgba(247, 242, 232, 0.9) 55%,
      rgba(247, 242, 232, 0.5) 100%
    );
  }

  .hero-banner__content {
    max-width: 100%;
    padding: calc(64px + env(safe-area-inset-top, 0px)) 20px 40px;
    justify-content: center;
    flex: 1;
    box-sizing: border-box;
  }

  .landing-flow {
    padding: 56px 0 20px;
  }

  .download-cards {
    grid-template-columns: 1fr;
  }
}
</style>
