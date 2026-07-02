<template>
  <div class="home-desktop">
    <!-- 中栏：最近笔记 + 快捷操作 -->
    <main class="middle-panel">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <div class="welcome-text">
          <h1 class="welcome-title">{{ greeting }}，{{ displayName }}</h1>
          <p class="welcome-subtitle">欢迎使用 NoteMind 智能笔记助手</p>
        </div>
        <AppLogo :size="64" />
      </div>

      <!-- 快捷操作 -->
      <div class="quick-actions">
        <h2 class="section-title">快捷操作</h2>
        <div class="actions-grid">
          <div class="action-card" @click="navigate('/notes/edit')">
            <div class="action-icon">
              <IconPlus :size="28" :color="ICON_COLOR" />
            </div>
            <div class="action-text">
              <div class="action-name">新建笔记</div>
              <div class="action-desc">创建一篇新笔记</div>
            </div>
          </div>

          <div class="action-card" @click="navigate('/ai/assistant')">
            <div class="action-icon">
              <IconAI :size="28" :color="ICON_COLOR" />
            </div>
            <div class="action-text">
              <div class="action-name">AI 助手</div>
              <div class="action-desc">智能问答与对话</div>
            </div>
          </div>

          <div class="action-card" @click="navigate('/ai/generate')">
            <div class="action-icon">
              <IconMagic :size="28" :color="ICON_COLOR" />
            </div>
            <div class="action-text">
              <div class="action-name">AI 生成</div>
              <div class="action-desc">使用AI生成内容</div>
            </div>
          </div>

          <div class="action-card" @click="navigate('/ai/summarize')">
            <div class="action-icon">
              <IconTrend :size="28" :color="ICON_COLOR" />
            </div>
            <div class="action-text">
              <div class="action-name">AI 摘要</div>
              <div class="action-desc">智能摘要生成</div>
            </div>
          </div>

          <div class="action-card" @click="navigate('/ai/translate')">
            <div class="action-icon">
              <IconTranslate :size="28" :color="ICON_COLOR" />
            </div>
            <div class="action-text">
              <div class="action-name">翻译</div>
              <div class="action-desc">多语言翻译</div>
            </div>
          </div>

          <div class="action-card" @click="navigate('/mindmap')">
            <div class="action-icon">
              <IconMindmap :size="28" :color="ICON_COLOR" />
            </div>
            <div class="action-text">
              <div class="action-name">思维导图</div>
              <div class="action-desc">可视化思维</div>
            </div>
          </div>

          <div class="action-card" @click="navigate('/kg')">
            <div class="action-icon">
              <IconKnowledgeGraph :size="28" :color="ICON_COLOR" />
            </div>
            <div class="action-text">
              <div class="action-name">知识图谱</div>
              <div class="action-desc">知识关联</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近笔记 -->
      <div class="recent-notes">
        <div class="section-header">
          <h2 class="section-title">最近笔记</h2>
          <el-button text @click="navigate('/notes')">查看全部</el-button>
        </div>

        <div class="notes-grid" v-loading="loadingNotes">
          <div
            v-for="note in recentNotes"
            :key="note.id"
            class="note-card"
            @click="openNote(note)"
          >
            <div class="note-card-title">{{ note.title || '未命名笔记' }}</div>
            <div class="note-card-preview">{{ getNotePreview(note.content) }}</div>
            <div class="note-card-meta">
              <span class="note-card-time">{{ formatNoteTime(note.updated_at || note.created_at) }}</span>
              <div class="note-card-tags">
                <span v-for="tag in (note.tags || []).slice(0, 2)" :key="tag" class="note-tag">{{ tag }}</span>
              </div>
            </div>
          </div>

          <div v-if="!loadingNotes && recentNotes.length === 0" class="empty-recent">
            <IconDocument :size="48" :color="ICON_COLOR" />
            <p>还没有笔记</p>
            <el-button type="primary" @click="navigate('/notes/edit')">
              <IconPlus :size="14" />
              创建第一个笔记
            </el-button>
          </div>
        </div>
      </div>
    </main>

    <aside class="right-panel">
      <div class="stats-section">
        <h3 class="panel-title">📊 统计信息</h3>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">📝</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.totalNotes }}</div>
              <div class="stat-label">总笔记数</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🔥</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.weeklyNew }}</div>
              <div class="stat-label">本周新增</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🤖</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.aiCalls }}</div>
              <div class="stat-label">AI 调用</div>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-section">
        <h3 class="panel-title">📈 每日新建笔记</h3>
        <div class="chart-container" ref="chartRef"></div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { noteApi } from '@/api/note'
import * as echarts from 'echarts'
import {
  AppLogo,
  IconPlus,
  IconAI,
  IconMagic,
  IconTrend,
  IconTranslate,
  IconMindmap,
  IconKnowledgeGraph,
  IconDocument
} from '@/components/icons'

defineOptions({
  name: 'HomeDesktop'
})

const ICON_COLOR = 'var(--color-pencil)'

const router = useRouter()
const userStore = useUserStore()

const recentNotes = ref([])
const loadingNotes = ref(false)

const stats = ref({
  totalNotes: 0,
  weeklyNew: 0,
  aiCalls: 0
})

const chartRef = ref(null)
let chartInstance = null

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const displayName = computed(() => {
  const u = userStore.user
  if (!u) return '用户'
  return u.nickname || u.username || (u.email ? u.email.split('@')[0] : '用户')
})

function navigate(path) {
  router.push(path)
}

function openNote(note) {
  router.push(`/notes/edit/${note.id}`)
}

function getNotePreview(content) {
  if (!content) return '暂无内容'
  const text = content.replace(/<[^>]*>/g, '')
  return text.length > 80 ? text.slice(0, 80) + '...' : text
}

function formatNoteTime(time) {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60 * 1000) return '刚刚'
  if (diff < 60 * 60 * 1000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 24 * 60 * 60 * 1000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 7 * 24 * 60 * 60 * 1000) return `${Math.floor(diff / 86400000)}天前`
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  return `${month}-${day}`
}

async function loadRecentNotes() {
  loadingNotes.value = true
  try {
    const res = await noteApi.searchNotes({ page: 1, pageSize: 6 })
    const notes = res.items || res.notes || res.data?.items || res.data?.notes || res.data || []
    recentNotes.value = notes.slice(0, 6)
  } catch (err) {
    console.error('加载最近笔记失败:', err)
  } finally {
    loadingNotes.value = false
  }
}

function initChart() {
  if (!chartRef.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  const option = {
    grid: {
      top: 20,
      right: 10,
      bottom: 30,
      left: 30
    },
    xAxis: {
      type: 'category',
      data: [],
      axisLabel: {
        fontSize: 11,
        color: 'var(--color-text-muted)'
      },
      axisLine: {
        lineStyle: {
          color: 'var(--color-muted)'
        }
      },
      axisTick: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: {
        fontSize: 11,
        color: 'var(--color-text-muted)'
      },
      splitLine: {
        lineStyle: {
          color: 'var(--color-muted)',
          type: 'dashed'
        }
      }
    },
    series: [
      {
        type: 'bar',
        data: [],
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: '#f97316' },
              { offset: 1, color: '#fb923c' }
            ]
          },
          borderRadius: [4, 4, 0, 0]
        },
        barWidth: '60%'
      }
    ],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'var(--color-card-bg)',
      borderColor: 'var(--color-pencil)',
      borderWidth: 2,
      textStyle: {
        color: 'var(--color-text-primary)',
        fontFamily: 'var(--font-body)'
      },
      formatter: (params) => {
        const data = params[0]
        return `<div style="padding: 4px 8px;">
          <div style="font-weight: 600; margin-bottom: 4px;">${data.name}</div>
          <div>新建笔记: <strong>${data.value}</strong> 篇</div>
        </div>`
      }
    }
  }
  
  chartInstance.setOption(option)
}

function updateChart(notes) {
  if (!chartInstance) return
  
  const days = []
  const counts = []
  const today = new Date()
  
  for (let i = 6; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    const dateStr = `${date.getMonth() + 1}/${date.getDate()}`
    days.push(dateStr)
    
    const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate())
    const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1)
    
    const count = notes.filter(n => {
      const created = new Date(n.created_at || n.updated_at || 0)
      return created >= dayStart && created < dayEnd
    }).length
    
    counts.push(count)
  }
  
  chartInstance.setOption({
    xAxis: { data: days },
    series: [{ data: counts }]
  })
}

async function loadStats() {
  try {
    const allNotesRes = await noteApi.getNotes()
    const allNotes = Array.isArray(allNotesRes) ? allNotesRes : (allNotesRes.items || allNotesRes.data || [])
    stats.value.totalNotes = allNotes.length

    const now = new Date()
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    stats.value.weeklyNew = allNotes.filter(n => {
      const createdAt = new Date(n.created_at || n.updated_at || 0)
      return createdAt >= weekAgo
    }).length

    const chatHistory = localStorage.getItem(`home_chat_history_u${userStore.user?.id}`)
    if (chatHistory) {
      try {
        const parsed = JSON.parse(chatHistory)
        const messages = Array.isArray(parsed) ? parsed : parsed.messages || []
        stats.value.aiCalls = messages.filter(m => m.role === 'assistant').length
      } catch {
        stats.value.aiCalls = 0
      }
    }
    
    await nextTick()
    updateChart(allNotes)
  } catch (err) {
    console.error('加载统计数据失败:', err)
  }
}

onMounted(async () => {
  await loadRecentNotes()
  await nextTick()
  initChart()
  await loadStats()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.home-desktop {
  display: flex;
  width: 100%;
  height: 100%;
  background: var(--color-content-bg);
  overflow: hidden;
}

/* 中栏 */
.middle-panel {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 24px 32px;
  background: var(--color-content-bg);
}

.welcome-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  background: var(--color-card-bg);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard-sm);
  margin-bottom: 24px;
}

.welcome-title {
  font-family: var(--font-heading);
  font-size: 28px;
  color: var(--color-pencil);
  margin: 0 0 8px 0;
}

.welcome-subtitle {
  font-family: var(--font-body);
  font-size: 16px;
  color: var(--color-text-secondary);
  margin: 0;
}

.section-title {
  font-family: var(--font-heading);
  font-size: 20px;
  color: var(--color-pencil);
  margin: 0 0 16px 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-header .section-title {
  margin: 0;
}

/* 快捷操作 */
.quick-actions {
  margin-bottom: 32px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--color-card-bg);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  box-shadow: var(--shadow-hard-sm);
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-card:hover {
  transform: translate(2px, 2px);
  box-shadow: var(--shadow-hard);
  background: var(--color-yellow);
}

.action-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--color-muted);
  border-radius: 12px;
  flex-shrink: 0;
}

.action-name {
  font-family: var(--font-heading);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-pencil);
  margin-bottom: 4px;
}

.action-desc {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 最近笔记 */
.recent-notes {
  margin-bottom: 24px;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.note-card {
  padding: 16px;
  background: var(--color-card-bg);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  box-shadow: var(--shadow-hard-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 140px;
}

.note-card:hover {
  transform: translate(2px, 2px);
  box-shadow: var(--shadow-hard);
  background: var(--color-yellow);
}

.note-card-title {
  font-family: var(--font-heading);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-pencil);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-card-preview {
  flex: 1;
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.note-card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--color-text-muted);
}

.note-card-tags {
  display: flex;
  gap: 4px;
}

.note-tag {
  padding: 2px 6px;
  background: var(--color-muted);
  border-radius: 4px;
  font-size: 11px;
  color: var(--color-pencil);
}

.empty-recent {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  gap: 12px;
  color: #888;
}

/* 右栏 */
.right-panel {
  width: 320px;
  background: var(--color-card-bg);
  border-left: 2px dashed var(--color-muted);
  overflow-y: auto;
  overflow-x: hidden;
  flex-shrink: 0;
  padding: 20px;
}

.panel-title {
  font-family: var(--font-heading);
  font-size: 16px;
  font-weight: 700;
  color: var(--color-heading);
  margin: 0 0 16px 0;
}

/* 统计信息 */
.stats-section {
  margin-bottom: 24px;
}

.stats-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--color-content-bg);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  box-shadow: var(--shadow-hard-sm);
}

.stat-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-family: var(--font-heading);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-pencil);
  line-height: 1.2;
}

.stat-label {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-text-muted);
}

/* 图表区域 */
.chart-section {
  margin-bottom: 20px;
}

.chart-container {
  width: 100%;
  height: 220px;
  background: var(--color-content-bg);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  padding: 8px;
  box-sizing: border-box;
}

@media (prefers-color-scheme: dark) {
  .action-icon {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .stat-card {
    background: rgba(0, 0, 0, 0.2);
  }
}
</style>