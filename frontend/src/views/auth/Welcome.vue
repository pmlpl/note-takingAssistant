<template>
  <div class="welcome-landing">
    <!-- ==================== NAVIGATION ==================== -->
    <header
      id="navbar"
      class="welcome-nav"
      :class="{ 'welcome-nav--scrolled': navScrolled }"
    >
      <div class="nav-inner">
        <div class="nav-brand" @click="scrollToTop">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--color-yellow)">
            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
            <path d="m15 5 4 4" />
          </svg>
          <span>NoteMind</span>
        </div>
        <nav class="nav-center-links">
          <a href="#features" class="nav-center-link">Features</a>
          <a href="#steps" class="nav-center-link">Steps</a>
          <a href="#stats" class="nav-center-link">Stats</a>
        </nav>
        <nav class="nav-links">
          <a
            class="nav-link-github"
            :href="GITHUB_REPO_URL"
            target="_blank"
            rel="noopener noreferrer"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            <span class="nav-github-text">GitHub</span>
          </a>
          <el-button link class="nav-btn-link" @click="navigate('/login')">登录</el-button>
          <el-button type="primary" class="nav-btn-primary" @click="navigate('/register')">
            免费注册
          </el-button>
        </nav>
      </div>
    </header>

    <!-- ==================== HERO SECTION ==================== -->
    <section
      id="hero"
      ref="heroSection"
      class="hero-banner"
      @mousemove="onHeroMouseMove"
      @mouseleave="onHeroMouseLeave"
      @mouseenter="onHeroMouseEnter"
    >
      <!-- Parallax background image -->
      <div
        ref="heroBg"
        class="hero-banner__bg"
        style="background-image: url('/welcome/welcome-hero-banner.png')"
      />
      <!-- Left gradient scrim -->
      <div class="hero-banner__scrim" />
      <!-- Bottom gradient -->
      <div class="hero-banner__bottom-fade" />

      <!-- Floating particles (CSS only) -->
      <div class="hero-particles" aria-hidden="true">
        <span class="float-particle" style="top:12%; left:8%; width:18px; height:18px; background:var(--color-yellow); animation-delay:0s; animation-duration:6s;" />
        <span class="float-particle" style="top:25%; left:75%; width:14px; height:14px; background:var(--color-blue); animation-delay:1.2s; animation-duration:7s;" />
        <span class="float-particle" style="top:60%; left:82%; width:20px; height:20px; background:var(--color-accent); animation-delay:0.6s; animation-duration:5.5s;" />
        <span class="float-particle" style="top:70%; left:15%; width:12px; height:12px; background:var(--color-green); animation-delay:1.8s; animation-duration:6.5s;" />
        <span class="float-particle" style="top:40%; left:55%; width:16px; height:16px; background:var(--color-yellow); animation-delay:2.4s; animation-duration:7.5s;" />
        <span class="float-particle" style="top:85%; left:45%; width:10px; height:10px; background:var(--color-blue); animation-delay:0.9s; animation-duration:5s;" />
      </div>

      <!-- Mouse-following glow blob -->
      <div
        class="hero-glow"
        :style="{ left: glowX + 'px', top: glowY + 'px', opacity: glowVisible ? 1 : 0 }"
        aria-hidden="true"
      />

      <!-- HERO CONTENT -->
      <div class="hero-banner__content">
        <!-- Tech badge -->
        <div class="hero-badge">
          <span class="hero-badge__dot" />
          <span>基于 Vue 3 + FastAPI 构建</span>
        </div>

        <!-- Typewriter title -->
        <h1 class="hero-title">
          <span class="typewriter-prefix">{{ typewriterPrefix }}</span>
          <span class="typewriter-suffix" :class="{ 'is-visible': typewriterDone }">学习搭档</span>
          <span v-if="!typewriterDone" class="typewriter-cursor">|</span>
        </h1>

        <!-- Subtitle (fades in after title) -->
        <p class="hero-subtitle" :class="{ 'is-visible': subtitleVisible }">
          NoteMind 帮你写笔记、做总结、画导图。Web 版需自带云端 API Key；桌面版可直连本机 LM Studio，AI 完全本地运行。
        </p>

        <!-- CTA buttons -->
        <div class="hero-cta" :class="{ 'is-visible': ctaVisible }">
          <a href="#" class="hero-cta-item hero-cta-item--primary" @click.prevent="navigate('/register')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
            </svg>
            免费开始使用
          </a>
          <a href="#" class="hero-cta-item hero-cta-item--outline" @click.prevent="navigate('/login')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            已有账号登录
          </a>
        </div>

        <!-- Tech strip chips -->
        <div class="hero-tech" :class="{ 'is-visible': techVisible }">
          <span v-for="(chip, index) in TECH_CHIPS" :key="chip" class="hero-chip" :style="{ '--chip-delay': `${getChipDelay(index)}s` }">
            {{ chip }}
          </span>
        </div>
      </div>

      <!-- Scroll down arrow -->
      <div class="hero-scroll-hint" aria-hidden="true">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 5v14" />
          <path d="m19 12-7 7-7-7" />
        </svg>
      </div>
    </section>

    <!-- ==================== FEATURES SECTION ==================== -->
    <section id="features" class="features-section">
      <div class="features-inner">
        <header class="section-header">
          <h2>四大核心能力</h2>
          <p>AI 赋能你的每一步学习</p>
        </header>

        <div class="features-grid">
          <WelcomeFeatureRow
            v-for="(feature, index) in WELCOME_FEATURES"
            :key="feature.title"
            :feature="feature"
            :reveal-class="index % 2 === 0 ? 'reveal-left' : 'reveal-right'"
            @navigate="navigate"
          />
        </div>
      </div>
    </section>

    <!-- ==================== STEPS SECTION ==================== -->
    <section id="steps" ref="stepsAnchor" class="steps-section" :class="{ 'is-visible': stepsVisible }">
      <div class="steps-inner">
        <header class="section-header">
          <h2>四步开始使用</h2>
          <p>简单四步，开启你的 AI 学习之旅</p>
        </header>

        <div class="steps-grid">
          <div
            v-for="(step, index) in HOW_IT_WORKS"
            :key="step.step"
            class="step-card reveal-up"
            :style="{ '--step-delay': `${index * 0.15}s` }"
          >
            <div class="step-header">
              <div class="step-number">{{ step.step }}</div>
              <div v-if="step.step < HOW_IT_WORKS.length" class="step-connector" />
            </div>
            <h3>{{ step.title }}</h3>
            <p>{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== STATS SECTION ==================== -->
    <section id="stats" ref="statsAnchor" class="stats-section" :class="{ 'is-visible': statsVisible }">
      <div class="stats-inner">
        <div class="stats-grid">
          <div
            v-for="(stat, index) in dynamicStats"
            :key="stat.label"
            class="stat-card reveal-up"
            :style="{ '--stat-delay': `${index * 0.15}s` }"
          >
            <div class="stat-number" :class="[`stat-number--${stat.color}`]">
              {{ statCounters[stat.label] ?? '0' }}{{ stat.suffix }}
            </div>
            <div class="stat-label-wrap">
              <span class="stat-label">{{ stat.label }}</span>
              <span class="stat-underline" />
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== CTA SECTION ==================== -->
    <section id="cta" ref="ctaAnchor" class="cta-section" :class="{ 'is-visible': ctaSectionVisible }">
      <!-- Decorative circles -->
      <div class="cta-decor-circle cta-decor-circle--top" aria-hidden="true" />
      <div class="cta-decor-circle cta-decor-circle--bottom" aria-hidden="true" />

      <div class="cta-inner">
        <h2>准备好提升学习效率了吗？</h2>
        <p>立即注册 NoteMind，让 AI 成为你的学习搭档，解锁更高效的笔记体验。</p>
        <div class="cta-actions">
          <a href="#" class="cta-btn cta-btn--primary" @click.prevent="navigate('/register')">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
            </svg>
            Register Now
          </a>
          <a class="cta-btn cta-btn--outline" :href="GITHUB_REPO_URL" target="_blank" rel="noopener noreferrer">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
            </svg>
            View on GitHub
          </a>
        </div>
      </div>
    </section>

    <!-- ==================== FOOTER ==================== -->
    <footer class="welcome-footer">
      <div class="footer-inner">
        <div class="footer-grid">
          <!-- Column 1: Product -->
          <div class="footer-col">
            <div class="footer-brand">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--color-yellow)">
                <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                <path d="m15 5 4 4" />
              </svg>
              <span>NoteMind</span>
            </div>
            <ul class="footer-links">
              <li><a href="#features">Features</a></li>
              <li><a href="#">Pricing</a></li>
              <li><a href="#">Changelog</a></li>
              <li><a href="#">Roadmap</a></li>
            </ul>
          </div>

          <!-- Column 2: Resources -->
          <div class="footer-col">
            <h4>Resources</h4>
            <ul class="footer-links">
              <li><a href="#">Documentation</a></li>
              <li><a href="#">API Reference</a></li>
              <li><a href="#">Blog</a></li>
              <li><a href="#">Community</a></li>
            </ul>
          </div>

          <!-- Column 3: Account -->
          <div class="footer-col">
            <h4>Account</h4>
            <ul class="footer-links">
              <li><a href="#" @click.prevent="navigate('/login')">Login</a></li>
              <li><a href="#" @click.prevent="navigate('/register')">Register</a></li>
              <li><a href="#">Settings</a></li>
              <li><a href="#">Help Center</a></li>
            </ul>
          </div>
        </div>
        <div class="footer-copyright">
          &copy; 2026 NoteMind. All rights reserved.
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import WelcomeFeatureRow from '@/components/welcome/WelcomeFeatureRow.vue'
import { useLazyReveal } from '@/composables/useLazyReveal'
import {
  WELCOME_FEATURES,
  GITHUB_REPO_URL,
  HOW_IT_WORKS,
  TECH_CHIPS,
} from '@/constants/welcomeLanding'

const router = useRouter()

// Navigation scroll state
const navScrolled = ref(false)

// Hero section refs
const heroSection = ref(null)
const heroBg = ref(null)

// Typewriter effect
const typewriterPrefix = ref('')
const typewriterDone = ref(false)
const subtitleVisible = ref(false)
const ctaVisible = ref(false)
const techVisible = ref(false)
const prefixText = '让 AI 成为你的'
let typewriterTimer = null

// Mouse glow effect
const glowX = ref(0)
const glowY = ref(0)
const glowVisible = ref(false)

// Scroll parallax
let scrollTicking = false

// Lazy reveal for sections
const { root: stepsAnchor, visible: stepsVisible } = useLazyReveal()
const { root: statsAnchor, visible: statsVisible } = useLazyReveal()
const { root: ctaAnchor, visible: ctaSectionVisible } = useLazyReveal()

// Stats data (driven by API, with fallback)
const dynamicStats = computed(() => [
  { label: 'Active Users', suffix: '+', color: 'blue' },
  { label: 'Notes Created', suffix: '+', color: 'green' },
  { label: 'AI Generations', suffix: '+', color: 'accent' },
  { label: 'Core Features', suffix: '', color: 'yellow' },
])

// Stats counter animation
const statCounters = ref({})
const statsAnimated = ref(false)
const statsApiData = ref({ user_count: 0, note_count: 0, ai_count: 0 })

// Fetch real stats from backend API
async function fetchStats() {
  try {
    const res = await fetch('/api/v1/public/welcome-stats')
    if (res.ok) {
      const data = await res.json()
      statsApiData.value = data
    }
  } catch {
    // API 不可用时保持 0
  }
}

function animateCounters() {
  const stats = [
    { label: 'Active Users', targetValue: statsApiData.value.user_count || 0, decimals: 0, color: 'blue' },
    { label: 'Notes Created', targetValue: statsApiData.value.note_count || 0, decimals: 0, color: 'green' },
    { label: 'AI Generations', targetValue: statsApiData.value.ai_count || 0, decimals: 0, color: 'accent' },
    { label: 'Core Features', targetValue: 4, decimals: 0, color: 'yellow' },
  ]
  stats.forEach((stat) => {
    const target = stat.targetValue
    const decimals = stat.decimals || 0
    const duration = 2000
    let startTime = null

    // 后缀由模板统一渲染（{{ stat.suffix }}），动画只产出数字，避免出现 289++ 双后缀
    function step(timestamp) {
      if (!startTime) startTime = timestamp
      const progress = Math.min((timestamp - startTime) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = eased * target

      if (decimals > 0) {
        statCounters.value[stat.label] = current.toFixed(decimals)
      } else {
        statCounters.value[stat.label] = Math.floor(current).toLocaleString()
      }

      if (progress < 1) {
        requestAnimationFrame(step)
      } else {
        if (decimals > 0) {
          statCounters.value[stat.label] = target.toFixed(decimals)
        } else {
          statCounters.value[stat.label] = target.toLocaleString()
        }
      }
    }

    requestAnimationFrame(step)
  })
}

// Watch for stats section becoming visible to trigger counter animation
watch(statsVisible, async (isVisible) => {
  if (isVisible && !statsAnimated.value) {
    statsAnimated.value = true
    await fetchStats()
    animateCounters()
  }
})

// Chip delays (matching design稿)
function getChipDelay(index) {
  const delays = [0.05, 0.12, 0.19, 0.26, 0.33]
  return delays[index] || 0.05 + index * 0.07
}

// Navigation
function navigate(path) {
  router.push(path)
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Typewriter animation
function startTypewriter() {
  let idx = 0
  function typeNext() {
    if (idx < prefixText.length) {
      typewriterPrefix.value += prefixText.charAt(idx)
      idx++
      typewriterTimer = setTimeout(typeNext, 80 + Math.random() * 40)
    } else {
      typewriterDone.value = true
      setTimeout(() => { subtitleVisible.value = true }, 200)
      setTimeout(() => { ctaVisible.value = true }, 400)
      setTimeout(() => { techVisible.value = true }, 600)
    }
  }
  typewriterTimer = setTimeout(typeNext, 500)
}

// Hero mouse effects
function onHeroMouseMove(e) {
  if (!heroSection.value) return
  const rect = heroSection.value.getBoundingClientRect()
  glowX.value = e.clientX - rect.left
  glowY.value = e.clientY - rect.top
}

function onHeroMouseLeave() {
  glowVisible.value = false
}

function onHeroMouseEnter() {
  glowVisible.value = true
}

// Scroll handler (parallax + nav state)
function onScroll() {
  scrollTicking = false
  const scrollY = window.scrollY || window.pageYOffset

  // Parallax
  if (heroBg.value) {
    heroBg.value.style.transform = `translateY(${scrollY * 0.5}px)`
  }

  // Nav scroll state
  navScrolled.value = scrollY > 24
}

function handleScroll() {
  if (!scrollTicking) {
    scrollTicking = true
    requestAnimationFrame(onScroll)
  }
}

// Smooth scroll for anchor links
function handleAnchorClick(e) {
  const href = e.currentTarget.getAttribute('href')
  if (!href || href === '#') return
  const target = document.querySelector(href)
  if (target) {
    e.preventDefault()
    const navHeight = 64
    const top = target.getBoundingClientRect().top + window.scrollY - navHeight
    window.scrollTo({ top, behavior: 'smooth' })
  }
}

onMounted(async () => {
  await nextTick()
  window.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll()
  startTypewriter()

  // Bind smooth scroll to nav center links
  document.querySelectorAll('.nav-center-link').forEach((link) => {
    link.addEventListener('click', handleAnchorClick)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  if (typewriterTimer) clearTimeout(typewriterTimer)
})
</script>

<style scoped>
/* ==================== BASE STYLES ==================== */
.welcome-landing {
  width: 100%;
  min-height: 100vh;
  background: var(--color-paper);
  color: var(--color-pencil);

  /* P2 评审 #7：收敛为单一 token 体系——纸色/字体/阴影/黄等共享 token 全部
     继承全局 style.css，不再本地覆盖；此处仅保留欢迎页专属扩展 token */
  --color-paper-light: #faf8f3;
  --color-paper-dot: #ddd6c8;
  --color-surface: rgba(255, 255, 255, 0.65);
  --color-surface-solid: #ffffff;
  --color-text-primary: #2d2d2d;
  --color-text-secondary: #555555;
  /* P2 评审 #8：footer 链接/版权于深底 #2d2d2d 由 #888(3.88:1) 提至 #9a9a9a(4.89:1) AA */
  --color-text-muted: #9a9a9a;
  --color-text-inverse: #f5f0e6;
  --color-border-light: rgba(45, 45, 45, 0.15);
  --color-border-medium: rgba(45, 45, 45, 0.25);
  --text-hero: clamp(40px, 6vw, 72px);
  --text-h1: clamp(32px, 5vw, 56px);
  --text-h2: clamp(28px, 4vw, 40px);
  --text-h3: clamp(20px, 2.5vw, 28px);
  --text-body: clamp(15px, 1.6vw, 17px);
  --text-small: clamp(12px, 1.2vw, 14px);
  --text-micro: 12px;
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-out-back: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --duration-fast: 0.25s;
  --duration-normal: 0.5s;
  --duration-slow: 0.8s;
  --max-width: 1200px;
  --nav-height: 64px;

  /* Remove global body dot-grid texture */
  background-image: none;
  background-size: auto;
}

/* Override body dot-grid inside welcome */
.welcome-landing {
  background-image: none !important;
}

/* Force correct fonts inside Welcome (override global style.css) */
.welcome-landing,
.welcome-landing *,
.welcome-landing *::before,
.welcome-landing *::after {
  font-family: var(--font-body);
}

.welcome-landing h1,
.welcome-landing h2,
.welcome-landing h3,
.welcome-landing h4,
.welcome-landing h5,
.welcome-landing h6,
.welcome-landing :deep(h1),
.welcome-landing :deep(h2),
.welcome-landing :deep(h3),
.welcome-landing :deep(h4),
.welcome-landing :deep(h5),
.welcome-landing :deep(h6) {
  font-family: var(--font-heading);
}

/* ==================== NAVIGATION ==================== */
.welcome-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  height: var(--nav-height);
  transition: background 0.3s ease, box-shadow 0.3s ease;
  contain: layout style;
}

.welcome-nav--scrolled {
  background: rgba(253, 251, 247, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 1px 0 var(--color-border-light);
}

.nav-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 clamp(24px, 4vw, 48px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--nav-height);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-pencil);
  transition: opacity 0.2s;
}

.nav-brand:hover {
  opacity: 0.8;
}

.nav-center-links {
  display: none;
}

@media (min-width: 768px) {
  .nav-center-links {
    display: flex;
    align-items: center;
    gap: 24px;
  }
}

.nav-center-link {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: opacity 0.2s;
}

.nav-center-link:hover {
  opacity: 0.8;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-link-github {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-family: var(--font-body);
  transition: opacity 0.2s;
}

.nav-link-github:hover {
  opacity: 0.8;
}

.nav-github-text {
  display: none;
}

@media (min-width: 640px) {
  .nav-github-text {
    display: inline;
  }
}

.nav-btn-link {
  font-size: 14px !important;
  padding: 6px 16px !important;
}

.nav-btn-primary {
  font-size: 14px !important;
  padding: 6px 16px !important;
  border-radius: 8px !important;
}

/* ==================== HERO SECTION ==================== */
.hero-banner {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  overflow: hidden;
  background: var(--color-paper);
  contain: layout style paint;
}

.hero-banner__bg {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  will-change: transform;
}

.hero-banner__scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, var(--color-paper) 0%, var(--color-paper) 45%, rgba(253,251,247,0.4) 65%, transparent 100%);
}

.hero-banner__bottom-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 128px;
  background: linear-gradient(0deg, var(--color-paper) 0%, transparent 100%);
}

/* Floating particles */
.hero-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.float-particle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.5;
  animation: floatUp var(--duration-slow) var(--ease-in-out) infinite;
}

@keyframes floatUp {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.4; }
  50% { transform: translateY(-24px) scale(1.15); opacity: 0.7; }
}

/* Mouse glow blob */
.hero-glow {
  position: absolute;
  width: 320px;
  height: 320px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(184,134,11,0.10) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 1;
  transition: left 0.15s ease-out, top 0.15s ease-out, opacity 0.3s ease;
}

/* Hero content */
.hero-banner__content {
  position: relative;
  z-index: 10;
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 clamp(24px, 4vw, 48px);
  width: 100%;
}

.hero-banner__content > * {
  max-width: 520px;
}

/* Tech badge */
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 9999px;
  margin-bottom: 24px;
  background: var(--color-surface-solid);
  border: 1px solid var(--color-border-light);
  box-shadow: var(--shadow-hard-sm);
}

.hero-badge__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-green);
}

.hero-badge span:last-child {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

/* Typewriter title */
.hero-title {
  font-family: var(--font-body);
  font-size: var(--text-hero);
  font-weight: 700;
  line-height: 1.1;
  color: var(--color-pencil);
  text-wrap: balance;
  word-break: keep-all;
  overflow-wrap: break-word;
  margin: 0 0 16px;
}

.typewriter-prefix {
  font-family: var(--font-body);
}

.typewriter-suffix {
  opacity: 0;
  background-image: linear-gradient(120deg, var(--color-accent) 0%, var(--color-yellow) 100%);
  background-size: 100% 3px;
  background-position: 0 100%;
  background-repeat: no-repeat;
  padding-bottom: 2px;
  transition: opacity 0.4s ease;
  animation: waveUnderline 2s ease-in-out infinite;
}

.typewriter-suffix.is-visible {
  opacity: 1;
}

@keyframes waveUnderline {
  0%, 100% { background-position: 0% 100%; background-size: 100% 3px; }
  50% { background-position: 100% 100%; background-size: 100% 3px; }
}

.typewriter-cursor {
  animation: blink 0.75s step-end infinite;
  font-weight: 300;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Subtitle */
.hero-subtitle {
  font-family: var(--font-body);
  font-size: var(--text-body);
  color: var(--color-text-secondary);
  margin: 0 0 32px;
  opacity: 0;
  transition: opacity 0.8s var(--ease-out-expo);
}

.hero-subtitle.is-visible {
  opacity: 1;
}

/* CTA buttons */
.hero-cta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
  opacity: 0;
  transition: opacity 0.6s var(--ease-out-expo);
}

.hero-cta.is-visible {
  opacity: 1;
}

.hero-cta-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  text-decoration: none;
  transition: box-shadow 0.2s, transform 0.2s;
}

.hero-cta-item--primary {
  background: var(--color-pencil);
  color: var(--color-text-inverse);
  box-shadow: var(--shadow-hard);
}

.hero-cta-item--primary:hover {
  box-shadow: var(--shadow-hard-hover);
}

.hero-cta-item--outline {
  background: var(--color-surface-solid);
  color: var(--color-pencil);
  border: 1px solid var(--color-border-medium);
  box-shadow: var(--shadow-hard-sm);
}

.hero-cta-item--outline:hover {
  box-shadow: var(--shadow-hard);
}

/* Tech chips */
.hero-tech {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.6s var(--ease-out-expo);
}

.hero-tech.is-visible {
  opacity: 1;
}

.hero-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 9999px;
  white-space: nowrap;
  background: var(--color-surface);
  color: var(--color-blue);
  border: 1px solid var(--color-border-light);
  transform: translateX(30px);
  opacity: 0;
  animation: slideFromRight 0.5s var(--ease-out-expo) forwards;
  animation-delay: var(--chip-delay);
}

@keyframes slideFromRight {
  from { transform: translateX(30px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* Scroll hint */
.hero-scroll-hint {
  position: absolute;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  color: var(--color-text-muted);
  animation: scrollBounce 2s var(--ease-in-out) infinite;
}

@keyframes scrollBounce {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(10px); }
}

/* ==================== SECTION HEADER ==================== */
.section-header {
  text-align: center;
  margin-bottom: 48px;
}

@media (min-width: 768px) {
  .section-header {
    margin-bottom: 64px;
  }
}

.section-header h2 {
  font-family: var(--font-heading);
  font-size: var(--text-h2);
  color: var(--color-pencil);
  margin: 0 0 8px;
  text-wrap: balance;
}

.section-header p {
  font-family: var(--font-body);
  font-size: var(--text-body);
  color: var(--color-text-secondary);
  margin: 0;
}

/* ==================== FEATURES SECTION ==================== */
.features-section {
  padding: 64px 0;
  background: var(--color-paper);
  contain: layout style paint;
}

@media (min-width: 768px) {
  .features-section {
    padding: 96px 0;
  }
}

.features-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 clamp(24px, 4vw, 48px);
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

@media (min-width: 768px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 32px;
  }
}

/* ==================== STEPS SECTION ==================== */
.steps-section {
  padding: 64px 0;
  background: var(--color-paper-light);
  contain: layout style paint;
  opacity: 0;
  transform: translateY(40px);
  transition: opacity var(--duration-normal) var(--ease-out-expo), transform var(--duration-normal) var(--ease-out-expo);
}

.steps-section.is-visible {
  opacity: 1;
  transform: translateY(0);
}

@media (min-width: 768px) {
  .steps-section {
    padding: 96px 0;
  }
}

.steps-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 clamp(24px, 4vw, 48px);
}

.steps-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

@media (min-width: 640px) {
  .steps-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .steps-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 32px;
  }
}

.step-card {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity var(--duration-normal) var(--ease-out-expo), transform var(--duration-normal) var(--ease-out-expo), box-shadow var(--duration-fast) var(--ease-out-expo);
  transition-delay: var(--step-delay);
}

.steps-section.is-visible .step-card {
  opacity: 1;
  transform: translateY(0);
}

.step-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-hard-hover);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid var(--color-accent);
  color: var(--color-accent);
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}

.step-connector {
  display: none;
  flex: 1;
  border-top: 2px dashed var(--color-border-medium);
}

@media (min-width: 1024px) {
  .step-connector {
    display: block;
  }
}

.step-card h3 {
  font-family: var(--font-heading);
  font-size: var(--text-h3);
  color: var(--color-pencil);
  margin: 0 0 8px;
}

.step-card p {
  font-family: var(--font-body);
  font-size: var(--text-body);
  color: var(--color-text-secondary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ==================== STATS SECTION ==================== */
.stats-section {
  padding: 64px 0;
  background: var(--color-paper);
  contain: layout style paint;
  opacity: 0;
  transform: translateY(40px);
  transition: opacity var(--duration-normal) var(--ease-out-expo), transform var(--duration-normal) var(--ease-out-expo);
}

.stats-section.is-visible {
  opacity: 1;
  transform: translateY(0);
}

@media (min-width: 768px) {
  .stats-section {
    padding: 96px 0;
  }
}

.stats-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 clamp(24px, 4vw, 48px);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

@media (min-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 32px;
  }
}

.stat-card {
  text-align: center;
  padding: 24px 16px;
  background: var(--color-surface-solid);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-wobbly-sm);
  box-shadow: var(--shadow-hard-sm);
  opacity: 0;
  transform: translateY(40px);
  transition: opacity var(--duration-normal) var(--ease-out-expo), transform var(--duration-normal) var(--ease-out-expo);
  transition-delay: var(--stat-delay);
}

.stats-section.is-visible .stat-card {
  opacity: 1;
  transform: translateY(0);
}

.stat-number {
  font-family: var(--font-heading);
  font-size: var(--text-h1);
  font-weight: 700;
  white-space: nowrap;
  margin-bottom: 4px;
}

.stat-number--blue { color: var(--color-blue); }
.stat-number--green { color: var(--color-green); }
.stat-number--accent { color: var(--color-accent); }
/* P2 评审 #9：黄色统计数字原 #f0c040 白底仅 1.7:1，改深金 --color-yellow-deep（3.25:1，大字号 ≥3:1） */
.stat-number--yellow { color: var(--color-yellow-deep); }

.stat-label-wrap {
  position: relative;
  display: inline-block;
  padding-bottom: 8px;
}

.stat-label {
  font-family: var(--font-body);
  font-size: var(--text-body);
  color: var(--color-text-secondary);
}

.stat-underline {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 48px;
  height: 2px;
  background: var(--color-yellow-deep);
}

/* ==================== CTA SECTION ==================== */
.cta-section {
  position: relative;
  overflow: hidden;
  padding: 64px 0;
  background: var(--color-pencil);
  contain: layout style paint;
  opacity: 0;
  transform: translateY(40px);
  transition: opacity var(--duration-normal) var(--ease-out-expo), transform var(--duration-normal) var(--ease-out-expo);
}

.cta-section.is-visible {
  opacity: 1;
  transform: translateY(0);
}

@media (min-width: 768px) {
  .cta-section {
    padding: 96px 0;
  }
}

.cta-decor-circle {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.cta-decor-circle--top {
  top: -60px;
  right: -60px;
  width: 160px;
  height: 160px;
  background: var(--color-accent);
  opacity: 0.2;
}

.cta-decor-circle--bottom {
  bottom: -40px;
  left: -40px;
  width: 112px;
  height: 112px;
  background: var(--color-yellow);
  opacity: 0.15;
}

.cta-inner {
  position: relative;
  z-index: 10;
  text-align: center;
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 clamp(24px, 4vw, 48px);
}

.cta-inner h2 {
  font-family: var(--font-heading);
  font-size: var(--text-h2);
  color: var(--color-text-inverse);
  margin: 0 0 12px;
  text-wrap: balance;
}

.cta-inner p {
  font-family: var(--font-body);
  font-size: var(--text-body);
  color: var(--color-paper-dot);
  margin: 0 auto 32px;
  max-width: 480px;
}

.cta-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.cta-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 32px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  text-decoration: none;
  transition: opacity 0.2s, box-shadow 0.2s;
}

.cta-btn--primary {
  background: var(--color-accent);
  color: var(--color-surface-solid);
  box-shadow: var(--shadow-hard);
}

.cta-btn--primary:hover {
  opacity: 0.9;
  box-shadow: var(--shadow-hard-hover);
}

.cta-btn--outline {
  background: transparent;
  color: var(--color-text-inverse);
  border: 1px solid var(--color-text-inverse);
}

.cta-btn--outline:hover {
  opacity: 0.9;
}

/* ==================== FOOTER ==================== */
.welcome-footer {
  padding: 48px 0;
  background: var(--color-pencil);
}

.footer-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 clamp(24px, 4vw, 48px);
}

.footer-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 32px;
}

@media (min-width: 640px) {
  .footer-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .footer-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 48px;
  }
}

.footer-col {
  min-width: 0;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-inverse);
}

.footer-col h4 {
  font-family: var(--font-body);
  font-size: var(--text-body);
  font-weight: 600;
  color: var(--color-text-inverse);
  margin: 0 0 16px;
}

.footer-links {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footer-links li {
  margin-bottom: 8px;
}

.footer-links a {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: opacity 0.2s;
}

.footer-links a:hover {
  opacity: 0.8;
}

.footer-copyright {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-medium);
  text-align: center;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-text-muted);
}

/* ==================== REDUCED MOTION ==================== */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>