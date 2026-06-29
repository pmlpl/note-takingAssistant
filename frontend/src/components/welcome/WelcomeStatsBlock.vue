<template>
  <section ref="root" class="stats-block" :class="{ 'is-visible': visible }">
    <header class="stats-header">
      <span class="stats-eyebrow">PLATFORM STATS</span>
      <h2>平台数据一览</h2>
      <p>近 30 日注册用户趋势（公开统计，无需登录）</p>
    </header>

    <div class="stats-body">
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
              <div class="stat-card__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
              </div>
              <div class="stat-card__content">
                <span class="stat-label">注册用户</span>
                <span class="stat-value">{{ stats.user_count }}</span>
                <span class="stat-hint">累计注册</span>
              </div>
            </div>
            <div class="stat-card stat-card--accent">
              <div class="stat-card__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                  <polyline points="17 6 23 6 23 12" />
                </svg>
              </div>
              <div class="stat-card__content">
                <span class="stat-label">近 30 日新增</span>
                <span class="stat-value">{{ usersRecent30 }}</span>
                <span class="stat-hint">新注册用户</span>
              </div>
            </div>
          </div>

          <div class="chart-panel">
            <div class="chart-panel__header">
              <div>
                <h3 class="chart-title">注册用户 · 每日新增</h3>
                <p class="chart-desc">柱状为当日新注册，折线为平台累计用户趋势</p>
              </div>
            </div>
            <div ref="userChartEl" class="chart-box" />
          </div>
        </template>
      </template>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue'
import { useLazyReveal } from '@/composables/useLazyReveal'
import { publicApi } from '@/api/public'
import {
  WELCOME_CHART,
  baseGrid,
  axisCategory,
  axisValue,
  tooltipAxis,
  legendBottom,
} from '@/utils/welcomeChartTheme'

const { root, visible } = useLazyReveal({ rootMargin: '0px 0px -5% 0px' })

const loading = ref(false)
const stats = ref({
  user_count: 0,
  daily_users: [],
})

const userChartEl = ref(null)
let userChart = null

const usersRecent30 = computed(() =>
  (stats.value.daily_users || []).reduce((s, d) => s + (d.new_users || 0), 0)
)

function formatDates(series) {
  return (series || []).map((d) => d.date.slice(5))
}

async function fetchStats() {
  loading.value = true
  try {
    stats.value = await publicApi.getWelcomeStats()
  } catch (e) {
    console.error('欢迎页统计加载失败', e)
    stats.value = { user_count: 0, daily_users: [] }
  } finally {
    loading.value = false
  }
}

async function renderUserChart() {
  if (!userChartEl.value) return
  const echartsNs = await import('echarts')
  const echarts = echartsNs.default ?? echartsNs
  const series = stats.value.daily_users || []
  if (!series.length) return

  userChart?.dispose()
  userChart = echarts.init(userChartEl.value)

  const dates = formatDates(series)
  const dailyNew = series.map((d) => d.new_users ?? 0)
  const totalNew = dailyNew.reduce((a, b) => a + b, 0)
  let cumulative = Math.max(0, (stats.value.user_count || 0) - totalNew)
  const cumLine = dailyNew.map((n) => {
    cumulative += n
    return cumulative
  })

  userChart.setOption({
    grid: baseGrid(),
    tooltip: tooltipAxis(),
    legend: legendBottom(['当日新增', '注册用户累计']),
    xAxis: axisCategory(dates),
    yAxis: [
      { ...axisValue('新增'), position: 'left' },
      {
        ...axisValue('累计'),
        position: 'right',
        splitLine: { show: false },
        axisLine: { show: false },
      },
    ],
    series: [
      {
        name: '当日新增',
        type: 'bar',
        barMaxWidth: 28,
        itemStyle: {
          color: WELCOME_CHART.yellow,
          borderColor: WELCOME_CHART.pencil,
          borderWidth: 2,
          borderRadius: [4, 4, 0, 0],
        },
        data: dailyNew,
      },
      {
        name: '注册用户累计',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 3, color: WELCOME_CHART.blue },
        itemStyle: { color: WELCOME_CHART.blue },
        data: cumLine,
      },
    ],
  })
}

watch(visible, (v) => {
  if (v) void fetchStats()
})

watch(
  () => [loading.value, stats.value.daily_users, visible.value],
  async ([isLoading, , vis]) => {
    if (vis && !isLoading) {
      await nextTick()
      await renderUserChart()
    }
  }
)

function onResize() {
  userChart?.resize()
}

watch(visible, (v) => {
  if (v) window.addEventListener('resize', onResize)
  else window.removeEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  userChart?.dispose()
  userChart = null
})

defineExpose({ visible })
</script>

<style scoped>
.stats-block {
  width: 100%;
  padding: 0 0 24px;
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.65s ease, transform 0.65s ease;
  box-sizing: border-box;
}

.stats-block.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.stats-header {
  text-align: center;
  padding: 40px 0 28px;
}

.stats-eyebrow {
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

.stats-header h2 {
  font-family: var(--font-heading);
  font-size: clamp(28px, 4vw, 36px);
  margin: 0 0 8px;
}

.stats-header p {
  margin: 0;
  color: #666;
  font-size: 15px;
}

.stats-body {
  background: rgba(255, 255, 255, 0.7);
  border: 2.5px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard-sm);
  padding: clamp(20px, 4vw, 32px) clamp(20px, 4vw, 36px) clamp(24px, 4vw, 32px);
  box-sizing: border-box;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  background: #faf9f6;
  transition: transform 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-card--accent {
  background: var(--color-yellow);
  border-color: var(--color-pencil);
}

.stat-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-wobbly-sm);
  background: rgba(45, 93, 161, 0.08);
  color: var(--color-blue);
  flex-shrink: 0;
}

.stat-card--accent .stat-card__icon {
  background: rgba(255, 77, 77, 0.08);
  color: var(--color-accent);
}

.stat-card__content {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 13px;
  color: #777;
  margin-bottom: 4px;
}

.stat-value {
  font-family: var(--font-heading);
  font-size: 32px;
  font-weight: 700;
  color: var(--color-pencil);
  line-height: 1.1;
}

.stat-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.chart-panel {
  padding: 20px;
  border: 2px dashed var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  background: var(--color-paper);
}

.chart-panel__header {
  margin-bottom: 16px;
}

.chart-title {
  font-family: var(--font-heading);
  font-size: 17px;
  margin: 0 0 4px;
}

.chart-desc {
  margin: 0;
  font-size: 12px;
  color: #888;
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
