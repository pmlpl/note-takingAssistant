<template>
  <article
    ref="root"
    class="feature-card tilt-card"
    :class="[revealClass, { 'is-visible': visible }]"
    @mousemove="onCardMouseMove"
    @mouseleave="onCardMouseLeave"
    :style="cardStyle"
  >
    <div class="tilt-card-shine" :style="shineStyle" />
    <div class="feature-card__body">
      <div class="feature-card__header">
        <div class="feature-icon" :style="{ background: iconBg }">
          <component :is="iconComponent" v-if="iconComponent" />
        </div>
        <div>
          <h3 class="feature-card__title">{{ feature.title }}</h3>
          <p class="feature-card__subtitle">{{ feature.subtitle }}</p>
        </div>
      </div>
      <p class="feature-desc">{{ feature.description }}</p>
      <img
        :src="feature.image"
        :alt="feature.title"
        class="feature-card__img"
        loading="lazy"
      />
      <a
        href="#"
        class="magnetic-btn"
        :style="magneticStyle"
        @click.prevent="handleCtaClick"
      >
        Try Now
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12h14"/>
          <path d="m12 5 7 7-7 7"/>
        </svg>
      </a>
    </div>
  </article>
</template>

<script setup>
import { ref, computed, watch, nextTick, h } from 'vue'
import { useRouter } from 'vue-router'
import { useLazyReveal } from '@/composables/useLazyReveal'

const props = defineProps({
  feature: { type: Object, required: true },
  revealClass: { type: String, default: 'reveal-left' },
})

const emit = defineEmits(['navigate'])

const router = useRouter()
const { root, visible } = useLazyReveal({ rootMargin: '0px 0px -5% 0px', threshold: 0.15 })

// 3D tilt state
const rotateX = ref(0)
const rotateY = ref(0)
const shineX = ref(50)
const shineY = ref(50)
const magneticX = ref(0)
const magneticY = ref(0)

// Card style for 3D transform
const cardStyle = computed(() => ({
  transform: visible.value
    ? `perspective(800px) rotateX(${rotateX.value}deg) rotateY(${rotateY.value}deg) scale3d(1.02, 1.02, 1.02)`
    : '',
}))

// Shine gradient position
const shineStyle = computed(() => ({
  '--shine-x': `${shineX.value}%`,
  '--shine-y': `${shineY.value}%`,
}))

// Magnetic button style
const magneticStyle = computed(() => ({
  transform: `translate(${magneticX.value}px, ${magneticY.value}px)`,
}))

// Icon background color (all use yellow per design)
const iconBg = 'var(--color-yellow)'

// Icon components based on feature.icon
const iconComponents = {
  sparkles: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'm12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z' }),
  ]),
  languages: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'm5 8 6 6' }),
    h('path', { d: 'm4 14 6-6 2-3' }),
    h('path', { d: 'M2 5h12' }),
    h('path', { d: 'M7 2h1' }),
    h('path', { d: 'm22 22-5-10-5 10' }),
    h('path', { d: 'M14 18h6' }),
  ]),
  gitBranch: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M12 2v20' }),
    h('path', { d: 'M17 5h3a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-3' }),
    h('path', { d: 'M17 15h3a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2h-3' }),
    h('path', { d: 'M7 5H4a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h3' }),
    h('path', { d: 'M7 15H4a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h3' }),
  ]),
  notebookPen: () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
    h('path', { d: 'M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H19a1 1 0 0 1 1 1v18a1 1 0 0 1-1 1H6.5a1 1 0 0 1 0-5H20' }),
    h('path', { d: 'M8 7h6' }),
    h('path', { d: 'M8 11h8' }),
  ]),
}

const iconComponent = computed(() => iconComponents[props.feature.icon] || iconComponents.sparkles)

// 3D tilt on mouse move
function onCardMouseMove(e) {
  if (!root.value) return
  const rect = root.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  const centerX = rect.width / 2
  const centerY = rect.height / 2

  rotateX.value = ((y - centerY) / centerY) * -8
  rotateY.value = ((x - centerX) / centerX) * 8
  shineX.value = (x / rect.width) * 100
  shineY.value = (y / rect.height) * 100

  // Magnetic button effect
  const btn = root.value.querySelector('.magnetic-btn')
  if (btn) {
    const btnRect = btn.getBoundingClientRect()
    const btnCX = btnRect.left + btnRect.width / 2
    const btnCY = btnRect.top + btnRect.height / 2
    const dist = Math.sqrt(Math.pow(e.clientX - btnCX, 2) + Math.pow(e.clientY - btnCY, 2))
    if (dist < 80) {
      const dx = (e.clientX - btnCX) * 0.15
      const dy = (e.clientY - btnCY) * 0.15
      const maxD = 8
      magneticX.value = Math.max(-maxD, Math.min(maxD, dx))
      magneticY.value = Math.max(-maxD, Math.min(maxD, dy))
    } else {
      magneticX.value = 0
      magneticY.value = 0
    }
  }
}

function onCardMouseLeave() {
  rotateX.value = 0
  rotateY.value = 0
  magneticX.value = 0
  magneticY.value = 0
}

function handleCtaClick() {
  if (props.feature.route) {
    emit('navigate', props.feature.route)
    router.push(props.feature.route)
  }
}
</script>

<style scoped>
@property --border-angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}

/* Reveal animations */
.feature-card {
  position: relative;
  overflow: hidden;
  background: var(--color-surface-solid);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard);
  opacity: 0;
  transform-style: preserve-3d;
  perspective: 800px;
  will-change: transform;
  transition: transform var(--duration-fast) var(--ease-out-expo), box-shadow var(--duration-fast) var(--ease-out-expo), opacity var(--duration-normal) var(--ease-out-expo);
}

/* Reveal classes (matching design稿) */
.feature-card.reveal-left {
  transform: translateX(-60px);
}

.feature-card.reveal-right {
  transform: translateX(60px);
}

.feature-card.is-visible {
  opacity: 1;
  transform: translateX(0) translateY(0);
}

.feature-card.is-visible.reveal-left,
.feature-card.is-visible.reveal-right {
  transform: translateX(0) translateY(0);
}

/* Animated gradient border on hover */
.feature-card::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  background: conic-gradient(from var(--border-angle, 0deg), var(--color-yellow), var(--color-blue), var(--color-accent), var(--color-green), var(--color-yellow));
  z-index: -1;
  opacity: 0;
  transition: opacity 0.4s ease;
}

.feature-card:hover::before {
  opacity: 1;
  animation: rotateBorder 3s linear infinite;
}

@keyframes rotateBorder {
  to { --border-angle: 360deg; }
}

.feature-card:hover {
  box-shadow: var(--shadow-hard-hover);
}

/* Shine effect */
.tilt-card-shine {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
  background: radial-gradient(circle at var(--shine-x, 50%) var(--shine-y, 50%), rgba(255,255,255,0.25) 0%, transparent 60%);
  z-index: 5;
}

.feature-card:hover .tilt-card-shine {
  opacity: 1;
}

.feature-card__body {
  padding: 24px;
  position: relative;
  z-index: 1;
}

/* Header with icon and title */
.feature-card__header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  color: var(--color-pencil);
  transition: transform 0.4s var(--ease-out-back);
}

.feature-card:hover .feature-icon {
  transform: scale(1.2) rotate(15deg);
}

.feature-card__title {
  font-family: var(--font-heading);
  font-size: var(--text-h3);
  color: var(--color-pencil);
  margin: 0;
}

.feature-card__subtitle {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 2px 0 0;
}

/* Description */
.feature-desc {
  font-family: var(--font-body);
  font-size: var(--text-body);
  color: var(--color-text-secondary);
  margin: 0 0 16px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: transform 0.4s ease;
}

.feature-card:hover .feature-desc {
  transform: translateY(-4px);
}

/* Feature image */
.feature-card__img {
  display: block;
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: var(--radius-wobbly-sm);
  margin-bottom: 16px;
  filter: grayscale(30%) blur(1px);
  transition: filter 0.4s ease, transform 0.4s ease;
}

.feature-card:hover .feature-card__img {
  filter: grayscale(0%) blur(0);
  transform: scale(1.03);
}

/* Magnetic button */
.magnetic-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-surface-solid);
  background: var(--color-blue);
  border-radius: 8px;
  text-decoration: none;
  font-family: var(--font-body);
  transition: transform 0.2s ease-out, opacity 0.2s ease;
}

.magnetic-btn:hover {
  opacity: 0.9;
}

@media (max-width: 768px) {
  .feature-card__img {
    height: 140px;
  }
}
</style>