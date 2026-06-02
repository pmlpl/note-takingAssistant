<template>
  <section ref="root" class="stats-block" :class="{ 'is-visible': visible }">
    <div class="stats-inner">
      <header class="stats-head">
        <h2>平台数据一览</h2>
        <p>近 30 日注册用户趋势（公开统计，无需登录）</p>
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
              <span class="stat-hint">累计</span>
            </div>
            <div class="stat-card stat-card--yellow">
              <span class="stat-label">近 30 日新增</span>
              <span class="stat-value">{{ usersRecent30 }}</span>
              <span class="stat-hint">新注册</span>
            </div>
          </div>

          <div class="chart-panel">
            <h3 class="chart-title">注册用户 · 每日新增</h3>
            <p class="chart-desc">柱状为当日新注册，折线为平台累计用户趋势</p>
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
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
  max-width: 520px;
  margin-left: auto;
  margin-right: auto;
}

.stat-card {
  text-align: center;
  padding: 18px 12px 14px;
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  background: #faf9f6;
}

.stat-card--yellow {
  background: var(--color-yellow);
}

.stat-label {
  display: block;
  font-size: 14px;
  color: #555;
  margin-bottom: 6px;
}

.stat-value {
  font-family: var(--font-heading);
  font-size: 34px;
  font-weight: 700;
  color: var(--color-pencil);
  line-height: 1.1;
}

.stat-hint {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: #888;
}

.chart-panel {
  padding: 16px 12px 8px;
  border: 2px dashed var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  background: var(--color-paper);
}

.chart-title {
  font-family: var(--font-heading);
  font-size: 18px;
  margin: 0 0 4px;
  text-align: center;
}

.chart-desc {
  margin: 0 0 12px;
  font-size: 12px;
  color: #777;
  text-align: center;
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
    max-width: none;
  }
  .chart-box {
    height: 220px;
  }
}
</style>
