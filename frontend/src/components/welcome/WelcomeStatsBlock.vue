<template>
  <section ref="root" class="stats-block" :class="{ 'is-visible': visible }">
    <div class="stats-inner">
      <header class="stats-head">
        <h2>平台数据一览</h2>
        <p>真实统计来自当前数据库（公开接口，无需登录）</p>
      </header>

      <div v-if="!visible" class="stats-skeleton">
        <el-skeleton :rows="4" animated />
      </div>

      <template v-else>
        <div v-if="loading" class="stats-skeleton">
          <el-skeleton :rows="4" animated />
        </div>
        <template v-else>
          <div class="stat-cards">
            <div class="stat-card">
              <span class="stat-label">注册用户</span>
              <span class="stat-value">{{ stats.user_count }}</span>
            </div>
            <div class="stat-card stat-card--yellow">
              <span class="stat-label">笔记总量</span>
              <span class="stat-value">{{ stats.note_count }}</span>
            </div>
            <div class="stat-card stat-card--blue">
              <span class="stat-label">近 30 日新增</span>
              <span class="stat-value">{{ recentTotal }}</span>
            </div>
          </div>
          <div ref="chartEl" class="chart-box" />
        </template>
      </template>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useLazyReveal } from '@/composables/useLazyReveal'
import { publicApi } from '@/api/public'

const { root, visible } = useLazyReveal({ rootMargin: '0px 0px -5% 0px' })

const loading = ref(false)
const stats = ref({ user_count: 0, note_count: 0, daily_new_notes: [] })
const chartEl = ref(null)
let chartInstance = null

const recentTotal = computed(() =>
  (stats.value.daily_new_notes || []).reduce((s, d) => s + (d.count || 0), 0)
)

async function fetchStats() {
  loading.value = true
  try {
    stats.value = await publicApi.getWelcomeStats()
  } catch (e) {
    console.error('欢迎页统计加载失败', e)
    stats.value = { user_count: 0, note_count: 0, daily_new_notes: [] }
  } finally {
    loading.value = false
  }
}

async function renderChart() {
  if (!chartEl.value || !stats.value.daily_new_notes?.length) return

  const echartsNs = await import('echarts')
  const echarts = echartsNs.default ?? echartsNs
  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartEl.value)

  const dates = stats.value.daily_new_notes.map((d) => d.date.slice(5))
  const counts = stats.value.daily_new_notes.map((d) => d.count)

  chartInstance.setOption({
    grid: { left: 48, right: 24, top: 32, bottom: 40 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#2d2d2d' } },
    },
    yAxis: {
      type: 'value',
      name: '新增笔记',
      minInterval: 1,
      splitLine: { lineStyle: { type: 'dashed', color: '#e5e0d8' } },
    },
    series: [
      {
        name: '每日新增',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 3, color: '#2d5da1' },
        itemStyle: { color: '#2d5da1' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(45, 93, 161, 0.35)' },
              { offset: 1, color: 'rgba(45, 93, 161, 0.02)' },
            ],
          },
        },
        data: counts,
      },
    ],
  })
}

watch(visible, (v) => {
  if (v) void fetchStats()
})

watch(
  () => [loading.value, stats.value.daily_new_notes, visible.value],
  async ([isLoading, , vis]) => {
    if (vis && !isLoading) {
      await renderChart()
    }
  }
)

function onResize() {
  chartInstance?.resize()
}

watch(visible, (v) => {
  if (v) window.addEventListener('resize', onResize)
  else window.removeEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chartInstance?.dispose()
  chartInstance = null
})

defineExpose({ visible })
</script>

<style scoped>
.stats-block {
  width: 100%;
  padding: 0 0 48px;
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.65s ease, transform 0.65s ease;
  box-sizing: border-box;
}

.stats-block.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.stats-inner {
  width: min(1100px, calc(100% - clamp(32px, 6vw, 80px)));
  max-width: 1100px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.72);
  border: 3px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard);
  padding: 32px clamp(20px, 4vw, 40px) 28px;
  box-sizing: border-box;
}

.stats-head {
  text-align: center;
  margin-bottom: 28px;
}

.stats-head h2 {
  font-family: var(--font-heading);
  font-size: 26px;
  margin: 0 0 6px;
}

.stats-head p {
  margin: 0;
  color: #666;
  font-size: 15px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  text-align: center;
  padding: 20px 12px;
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  background: #faf9f6;
}

.stat-card--yellow {
  background: var(--color-yellow);
}

.stat-card--blue {
  background: rgba(45, 93, 161, 0.12);
}

.stat-label {
  display: block;
  font-size: 14px;
  color: #555;
  margin-bottom: 8px;
}

.stat-value {
  font-family: var(--font-heading);
  font-size: 36px;
  font-weight: 700;
  color: var(--color-pencil);
}

.chart-box {
  width: 100%;
  height: 280px;
}

.stats-skeleton {
  padding: 12px 0;
}

@media (max-width: 640px) {
  .stat-cards {
    grid-template-columns: 1fr;
  }
  .chart-box {
    height: 220px;
  }
}
</style>
