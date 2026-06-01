import { ref, onMounted, onBeforeUnmount } from 'vue'

/**
 * 区块进入视口后再标记 visible，用于欢迎页分段加载与动画。
 */
export function useLazyReveal(options = {}) {
  const root = ref(null)
  const visible = ref(false)
  let observer

  onMounted(() => {
    const el = root.value
    if (!el) return

    observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          visible.value = true
          observer?.disconnect()
          observer = null
        }
      },
      {
        root: options.root ?? null,
        rootMargin: options.rootMargin ?? '0px 0px -8% 0px',
        threshold: options.threshold ?? 0.12,
      }
    )
    observer.observe(el)
  })

  onBeforeUnmount(() => {
    observer?.disconnect()
  })

  return { root, visible }
}
