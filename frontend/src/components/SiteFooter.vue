<template>
  <footer class="site-footer">
    <div class="site-footer__accent" aria-hidden="true" />
    <div class="site-footer__inner">
      <div class="site-footer__grid">
        <div class="site-footer__brand">
          <button type="button" class="brand-lockup" @click="onBrandClick">
            <AppLogo :size="28" />
            <span class="brand-name">智能笔记助手</span>
          </button>
          <p class="brand-tagline">AI 驱动的个人笔记与学习助手<br />基于 Vue 3 + FastAPI 全栈构建</p>
          <a
            class="brand-github"
            :href="GITHUB_REPO_URL"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="GitHub 开源仓库"
            title="GitHub"
          >
            <IconGitHub :size="24" color="currentColor" />
            <span>Star on GitHub</span>
          </a>
        </div>

        <div
          v-for="group in FOOTER_NAV_GROUPS"
          :key="group.id"
          class="site-footer__col"
        >
          <h3 class="col-title">{{ group.title }}</h3>
          <ul class="col-links">
            <li v-for="link in group.links" :key="link.label">
              <a
                v-if="link.external"
                :href="link.external"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ link.label }}
              </a>
              <a
                v-else-if="link.anchor"
                :href="link.anchor"
                @click.prevent="onAnchor(link.anchor)"
              >
                {{ link.label }}
              </a>
              <button
                v-else-if="link.route"
                type="button"
                class="col-link-btn"
                @click="onRoute(link.route)"
              >
                {{ link.label }}
              </button>
            </li>
          </ul>
        </div>
      </div>

      <div class="site-footer__bottom">
        <p class="copyright">© {{ year }} 智能笔记助手 · All rights reserved</p>
        <p class="credit">Made with Vue 3 + FastAPI</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { AppLogo, IconGitHub } from '@/components/icons'
import { FOOTER_NAV_GROUPS, GITHUB_REPO_URL } from '@/constants/welcomeLanding'

const emit = defineEmits(['navigate', 'scroll-top'])

const router = useRouter()
const year = computed(() => new Date().getFullYear())

function onBrandClick() {
  emit('scroll-top')
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onRoute(path) {
  emit('navigate', path)
  router.push(path)
}

function onAnchor(anchor) {
  const el = document.querySelector(anchor)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    return
  }
  onBrandClick()
}
</script>

<style scoped>
.site-footer {
  --footer-bg: #1e1e1e;
  --footer-text: #f5f0e6;
  --footer-muted: rgba(245, 240, 230, 0.6);
  --footer-accent: #c45c26;
  width: 100%;
  margin-top: 0;
  color: var(--footer-text);
  box-sizing: border-box;
}

.site-footer__accent {
  height: 4px;
  width: 100%;
  background: linear-gradient(
    90deg,
    var(--footer-accent) 0%,
    var(--color-accent) 50%,
    var(--footer-accent) 100%
  );
}

.site-footer__inner {
  background: var(--footer-bg);
  padding: 48px clamp(20px, 5vw, 48px) 28px;
}

.site-footer__grid {
  display: grid;
  grid-template-columns: 1.4fr repeat(3, 1fr);
  gap: 32px 24px;
  max-width: 1200px;
  margin: 0 auto 36px;
}

.site-footer__brand {
  min-width: 0;
}

.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  margin: 0 0 12px;
  border: none;
  background: none;
  cursor: pointer;
  color: inherit;
  font-family: var(--font-heading);
  font-size: 20px;
  transition: opacity 0.2s;
}

.brand-lockup:hover {
  opacity: 0.8;
}

.brand-tagline {
  margin: 0 0 16px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--footer-muted);
  max-width: 280px;
}

.brand-github {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--footer-text);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 18px;
  border: 2px solid rgba(245, 240, 230, 0.2);
  border-radius: var(--radius-wobbly-sm);
  background: rgba(255, 255, 255, 0.04);
  transition: color 0.2s ease, background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.brand-github:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--footer-accent);
  transform: translateY(-2px);
}

.col-title {
  font-family: var(--font-heading);
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 14px;
  color: var(--footer-text);
}

.col-links {
  list-style: none;
  margin: 0;
  padding: 0;
}

.col-links li + li {
  margin-top: 10px;
}

.col-links a,
.col-link-btn {
  font-size: 14px;
  color: var(--footer-muted);
  text-decoration: none;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-family: inherit;
  line-height: 1.4;
  transition: color 0.2s;
}

.col-links a:hover,
.col-link-btn:hover {
  color: var(--footer-text);
}

.site-footer__bottom {
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 24px;
  border-top: 1px solid rgba(245, 240, 230, 0.12);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px 24px;
  font-size: 13px;
  color: var(--footer-muted);
}

.copyright,
.credit {
  margin: 0;
}

@media (max-width: 768px) {
  .site-footer__grid {
    grid-template-columns: 1fr 1fr;
  }

  .site-footer__brand {
    grid-column: 1 / -1;
  }
}

@media (max-width: 480px) {
  .site-footer__grid {
    grid-template-columns: 1fr;
  }

  .site-footer__bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
