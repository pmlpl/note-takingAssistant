<template>
  <section
    ref="root"
    class="feature-row"
    :class="[{ 'is-visible': visible, 'feature-row--reverse': feature.reverse }]"
  >
    <div class="feature-inner">
      <div class="feature-media">
        <div v-if="visible && !imageReady && !imageError" class="media-placeholder" />
        <img
          v-if="visible"
          ref="imgRef"
          :src="feature.image"
          :alt="feature.title"
          class="feature-img"
          :class="{ 'feature-img--ready': imageReady }"
          decoding="async"
          @load="markImageReady"
          @error="onImageError"
        />
        <p v-if="imageError" class="media-error">图片加载失败，请刷新重试</p>
      </div>
      <div class="feature-copy">
        <span class="feature-tag">{{ feature.subtitle }}</span>
        <h3>{{ feature.title }}</h3>
        <p>{{ feature.description }}</p>
        <el-button
          v-if="feature.external"
          type="primary"
          class="feature-cta"
          @click="openExternal(feature.external)"
        >
          {{ feature.cta }}
        </el-button>
        <el-button
          v-else
          type="primary"
          class="feature-cta"
          @click="$emit('navigate', feature.route)"
        >
          {{ feature.cta }}
        </el-button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useLazyReveal } from '@/composables/useLazyReveal'

const props = defineProps({
  feature: { type: Object, required: true },
})

defineEmits(['navigate'])

const { root, visible } = useLazyReveal({ rootMargin: '0px 0px -8% 0px', threshold: 0.08 })
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
.feature-row {
  width: 100%;
  padding: 8px clamp(20px, 4vw, 48px) 36px;
  margin: 0;
  opacity: 0;
  transform: translateY(36px);
  transition: opacity 0.7s ease, transform 0.7s ease;
}

.feature-row.is-visible {
  opacity: 1;
  transform: translateY(0);
}

/* 区块之间的短虚线（非通栏黑线） */
.feature-row + .feature-row::before {
  content: '';
  display: block;
  width: min(260px, 36vw);
  margin: 0 auto 32px;
  border-top: 2px dashed rgba(45, 45, 45, 0.38);
}

.feature-inner {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: clamp(24px, 4vw, 48px);
  align-items: center;
}

.feature-row--reverse .feature-media {
  order: 2;
}

.feature-row--reverse .feature-copy {
  order: 1;
}

.feature-media {
  position: relative;
  border: 3px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard);
  overflow: hidden;
  background: #fff;
  min-height: 240px;
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
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

.feature-img {
  display: block;
  width: 100%;
  height: auto;
  vertical-align: middle;
  opacity: 0;
  transition: opacity 0.45s ease;
}

.feature-img--ready {
  opacity: 1;
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

.feature-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 8px 0;
  background: transparent;
}

.feature-copy h3 {
  font-family: var(--font-heading);
  font-size: clamp(24px, 3vw, 32px);
  margin: 8px 0 16px;
}

.feature-tag {
  display: inline-block;
  font-size: 13px;
  padding: 4px 12px;
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  background: var(--color-yellow);
  width: fit-content;
}

.feature-copy p {
  font-size: clamp(15px, 1.6vw, 17px);
  line-height: 1.75;
  color: #444;
  margin: 0 0 24px;
  max-width: 52ch;
}

.feature-cta {
  font-size: 16px !important;
  width: fit-content;
}

@media (max-width: 768px) {
  .feature-inner {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .feature-media {
    min-height: 200px;
  }

  .feature-row--reverse .feature-media,
  .feature-row--reverse .feature-copy {
    order: unset;
  }

  .feature-copy {
    padding: 0 4px 8px;
  }

  .feature-copy p {
    max-width: none;
  }
}
</style>
