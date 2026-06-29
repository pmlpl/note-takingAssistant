<template>
  <article
    ref="root"
    class="feature-card"
    :class="{ 'is-visible': visible }"
  >
    <div class="feature-card__media">
      <div v-if="visible && !imageReady && !imageError" class="media-placeholder" />
      <img
        v-if="visible"
        ref="imgRef"
        :src="feature.image"
        :alt="feature.title"
        class="feature-card__img"
        :class="{ 'feature-card__img--ready': imageReady }"
        decoding="async"
        @load="markImageReady"
        @error="onImageError"
      />
      <p v-if="imageError" class="media-error">图片加载失败，请刷新重试</p>
    </div>
    <div class="feature-card__body">
      <div class="feature-card__tag">{{ feature.subtitle }}</div>
      <h3 class="feature-card__title">{{ feature.title }}</h3>
      <p class="feature-card__desc">{{ feature.description }}</p>
      </div>
  </article>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useLazyReveal } from '@/composables/useLazyReveal'

const props = defineProps({
  feature: { type: Object, required: true },
})

defineEmits(['navigate'])

const { root, visible } = useLazyReveal({ rootMargin: '0px 0px -5% 0px', threshold: 0.08 })
const imgRef = ref(null)
const imageReady = ref(false)
const imageError = ref(false)

function markImageReady() {
  imageReady.value = true
  imageError.value = false
}

function onImageError() {
  imageError.value = true
  imageReady.value = false
}

async function syncImageFromCache() {
  await nextTick()
  const el = imgRef.value
  if (el?.complete && el.naturalWidth > 0) {
    markImageReady()
  }
}

watch(visible, (v) => {
  if (!v) return
  imageReady.value = false
  imageError.value = false
  void syncImageFromCache()
})

function openExternal(url) {
  window.open(url, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.feature-card {
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.7);
  border: 2.5px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard-sm);
  overflow: hidden;
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.6s ease, transform 0.6s ease, box-shadow 0.3s ease;
  cursor: default;
}

.feature-card:hover {
  box-shadow: var(--shadow-hard);
  transform: translateY(-4px);
}

.feature-card.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.feature-card.is-visible:hover {
  transform: translateY(-4px);
}

/* ── 图片区 ── */
.feature-card__media {
  position: relative;
  overflow: hidden;
  min-height: 180px;
  background: #f0ebe3;
}

.media-placeholder {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: linear-gradient(110deg, #f0ebe3 25%, #faf8f5 50%, #f0ebe3 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s ease-in-out infinite;
  pointer-events: none;
}

@keyframes shimmer {
  0% { background-position: 100% 0; }
  100% { background-position: -100% 0; }
}

.feature-card__img {
  display: block;
  width: 100%;
  height: auto;
  min-height: 180px;
  object-fit: cover;
  vertical-align: middle;
  opacity: 0;
  transition: opacity 0.45s ease, transform 0.5s ease;
}

.feature-card__img--ready {
  opacity: 1;
}

.feature-card:hover .feature-card__img--ready {
  transform: scale(1.03);
}

.media-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 16px;
  text-align: center;
  font-size: 14px;
  color: #888;
  background: #faf9f6;
}

/* ── 文案区 ── */
.feature-card__body {
  padding: 20px clamp(20px, 3vw, 28px) 24px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.feature-card__tag {
  display: inline-block;
  align-self: flex-start;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 12px;
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  background: var(--color-yellow);
  margin-bottom: 12px;
  letter-spacing: 0.02em;
}

.feature-card__title {
  font-family: var(--font-heading);
  font-size: clamp(20px, 2.5vw, 26px);
  margin: 0 0 12px;
  line-height: 1.25;
}

.feature-card__desc {
  font-size: 14px;
  line-height: 1.7;
  color: #555;
  margin: 0 0 20px;
  flex: 1;
}

.feature-card__cta {
  align-self: flex-start;
  font-size: 14px !important;
}

@media (max-width: 768px) {
  .feature-card__media {
    min-height: 160px;
  }
}
</style>
