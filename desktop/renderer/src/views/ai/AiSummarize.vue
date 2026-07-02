<template>
    <div class="ai-summarize-page">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="page-title">
          <el-button link @click="goBack" class="back-btn">
            <el-icon size="16"><DArrowLeft /></el-icon>
            <span>返回</span>
          </el-button>
          <h2><IconTrend :size="36" color="#f5a623" /> AI 笔记总结</h2>
        </div>
        <div class="page-subtitle">
          <p>智能分析笔记内容，提供总结、字数统计和优化建议</p>
        </div>
      </div>

      <el-row :gutter="20">
        <!-- 左侧：输入区 -->
        <el-col :xs="24" :lg="10">
          <el-card class="input-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span>📄 选择笔记</span>
              </div>
            </template>
            
            <el-form :model="form" label-width="90px">
              <el-form-item label="选择笔记" required>
                <el-select 
                  v-model="form.noteId" 
                  placeholder="请选择要总结的笔记"
                  style="width: 100%"
                  @change="handleNoteSelect"
                >
                  <el-option 
                    v-for="note in notes" 
                    :key="note.id" 
                    :label="note.title" 
                    :value="note.id" 
                  />
                </el-select>
              </el-form-item>
              
              <el-form-item label="或输入文本">
                <el-input 
                  v-model="form.content" 
                  type="textarea"
                  :rows="8"
                  placeholder="也可以直接粘贴要分析的文本内容"
                  maxlength="5000"
                  show-word-limit
                />
              </el-form-item>

              <el-form-item>
                <el-button 
                  type="primary" 
                  @click="analyzeNote" 
                  :loading="loading"
                  size="large"
                  class="analyze-btn"
                  :disabled="!canAnalyze"
                >
                  <IconTrend :size="18" />
                  {{ loading ? "AI分析中..." : "开始分析" }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <!-- 右侧：分析结果区 -->
        <el-col :xs="24" :lg="14">
          <!-- 分析结果 -->
          <el-card class="result-card" shadow="hover" v-if="analysisResult">
            <template #header>
              <div class="card-header result-header">
                <span>✨ 分析结果</span>
                <el-button 
                  size="default"
                  @click="copyAnalysis"
                >
                  📋 复制结果
                </el-button>
              </div>
            </template>
            
            <div class="analysis-content">
              <!-- 0. 评分雷达图 -->
              <div class="analysis-section">
                <h3 class="section-title">
                  <el-icon><MagicStick /></el-icon>
                  笔记质量评估
                </h3>
                <div class="section-body">
                  <div ref="radarChartRef" class="radar-chart"></div>
                  <div class="radar-legend">
                    <div class="legend-item">
                      <span class="legend-color before"></span>
                      <span>改进前评分</span>
                    </div>
                    <div class="legend-item">
                      <span class="legend-color after"></span>
                      <span>改进后预测</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 1. 内容总结 -->
              <div class="analysis-section">
                <h3 class="section-title">
                  <el-icon><Document /></el-icon>
                  内容总结
                </h3>
                <div class="section-body">
                  <p>{{ analysisResult.summary }}</p>
                </div>
              </div>

              <!-- 2. 字数统计 -->
              <div class="analysis-section">
                <h3 class="section-title">
                  <el-icon><ScaleToOriginal /></el-icon>
                  字数统计
                </h3>
                <div class="section-body stats-grid">
                  <div class="stat-item">
                    <div class="stat-value">{{ analysisResult.totalChars }}</div>
                    <div class="stat-label">总字符数</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ analysisResult.chineseChars }}</div>
                    <div class="stat-label">中文字符</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ analysisResult.englishWords }}</div>
                    <div class="stat-label">英文单词</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ analysisResult.paragraphs }}</div>
                    <div class="stat-label">段落数</div>
                  </div>
                </div>
              </div>

              <!-- 3. 优化建议 -->
              <div class="analysis-section">
                <h3 class="section-title">
                  <el-icon><MagicStick /></el-icon>
                  优化建议
                </h3>
                <div class="section-body suggestions">
                  <!-- 优点 -->
                  <div class="suggestion-group good">
                    <h4>✅ 做得好的地方</h4>
                    <ul>
                      <li v-for="(good, index) in analysisResult.strengths" :key="index">
                        {{ good }}
                      </li>
                    </ul>
                  </div>
                  
                  <!-- 不足 -->
                  <div class="suggestion-group improve">
                    <h4>💡 可以改进的地方</h4>
                    <ul>
                      <li v-for="(weakness, index) in analysisResult.weaknesses" :key="index">
                        {{ weakness }}
                      </li>
                    </ul>
                  </div>
                  
                  <!-- 具体建议 -->
                  <div class="suggestion-group tips">
                    <h4>📝 修改建议</h4>
                    <ul>
                      <li v-for="(tip, index) in analysisResult.suggestions" :key="index">
                        {{ tip }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 空状态 -->
          <el-card class="empty-card" v-else shadow="hover">
            <div class="empty-state">
              <IconTrend :size="80" color="#d9d9d9" />
              <h3>等待分析</h3>
              <p>在左侧选择笔记或输入文本，点击“开始分析”按钮</p>
              <p class="hint">💡 AI 将为您提供内容总结、字数统计和优化建议</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import { noteApi } from '@/api/note'
import { aiApi } from '@/api/ai'
import { IconTrend } from '@/components/icons'
import { DArrowLeft, Document, ScaleToOriginal, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

defineOptions({
  name: 'AiSummarize'
})

const router = useRouter()
const userStore = useUserStore()
/** keep-alive：切换账号后清空表单与分析结果 */
const summarizeBoundUserId = ref(null)

const notes = ref([])
const loading = ref(false)
const analysisResult = ref(null)
const radarChartRef = ref(null)  // 雷达图容器引用
let radarChart = null  // ECharts 实例
let radarResizeObserver = null
let radarWindowResizeHandler = null

function cleanupRadarChartSizing() {
  if (radarResizeObserver) {
    radarResizeObserver.disconnect()
    radarResizeObserver = null
  }
  if (radarWindowResizeHandler) {
    window.removeEventListener('resize', radarWindowResizeHandler)
    radarWindowResizeHandler = null
  }
}

function attachRadarChartSizing(chart) {
  cleanupRadarChartSizing()
  const el = radarChartRef.value
  if (!el) return
  radarResizeObserver = new ResizeObserver(() => {
    chart?.resize()
  })
  radarResizeObserver.observe(el)
  radarWindowResizeHandler = () => chart?.resize()
  window.addEventListener('resize', radarWindowResizeHandler)
}

/** Wait until the chart DOM has non-zero size (avoids ECharts clientWidth/height warning). */
async function ensureRadarContainerHasLayout(el) {
  await nextTick()
  await new Promise((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(resolve))
  })
  if (el.clientWidth > 0 && el.clientHeight > 0) return
  await new Promise((resolve) => {
    let settled = false
    const finish = () => {
      if (settled) return
      settled = true
      ro.disconnect()
      clearTimeout(timer)
      resolve()
    }
    const ro = new ResizeObserver(() => {
      if (el.clientWidth > 0 && el.clientHeight > 0) finish()
    })
    ro.observe(el)
    const timer = setTimeout(finish, 2000)
  })
}

const form = ref({
  noteId: '',
  content: ''
})

const canAnalyze = computed(() => {
  return form.value.noteId || form.value.content.trim().length > 0
})

onMounted(async () => {
  await refreshSummarizeSession()
})

onActivated(async () => {
  await refreshSummarizeSession()
})

async function refreshSummarizeSession() {
  const uid = userStore.user?.id
  if (uid == null || uid === undefined) return
  const uidNum = Number(uid)
  if (summarizeBoundUserId.value !== uidNum) {
    summarizeBoundUserId.value = uidNum
    form.value = { noteId: '', content: '' }
    analysisResult.value = null
    cleanupRadarChartSizing()
    if (radarChart) {
      radarChart.dispose()
      radarChart = null
    }
  }
  await loadNotes()
}

onBeforeUnmount(() => {
  cleanupRadarChartSizing()
  if (radarChart) {
    radarChart.dispose()
    radarChart = null
  }
})

async function loadNotes() {
  try {
    const data = await noteApi.getNotes()
    notes.value = data
  } catch (error) {
    console.error('加载笔记失败:', error)
    ElMessage.error('加载笔记失败')
  }
}

function handleNoteSelect(noteId) {
  // 选择笔记后清空手动输入的文本
  if (noteId) {
    form.value.content = ''
  }
}

function goBack() {
  router.back()
}

async function analyzeNote() {
  if (!canAnalyze.value) {
    ElMessage.warning('请选择笔记或输入文本')
    return
  }
  
  loading.value = true
  try {
    let contentToAnalyze = form.value.content
    
    // 如果选择了笔记，获取笔记内容
    if (form.value.noteId) {
      const note = await noteApi.getNote(form.value.noteId)
      contentToAnalyze = note.content
    }
    
    if (!contentToAnalyze || contentToAnalyze.trim().length === 0) {
      ElMessage.warning('内容为空，无法分析')
      return
    }
    
    // 调用 AI 分析 API
    const response = await aiApi.summarizeNote({ 
      content: contentToAnalyze 
    })
    
    // 计算字数统计
    const stats = calculateStats(contentToAnalyze)
    
    // 生成评分数据（6个维度）
    const scores = generateScores(response.data)
    
    // 组合分析结果（注意：response.data 才是实际的AI分析结果）
    analysisResult.value = {
      summary: response.data.summary || '暂无总结',
      ...stats,
      strengths: response.data.strengths || ['笔记结构清晰'],
      weaknesses: response.data.weaknesses || ['可以增加更多实例'],
      suggestions: response.data.suggestions || ['建议补充相关案例'],
      scores: scores  // 添加评分数据
    }
    
    ElMessage.success('分析完成！')
    
    // 等待 DOM 更新后渲染雷达图
    await nextTick()
    await renderRadarChart(scores)
  } catch (error) {
    console.error('分析失败:', error)
    ElMessage.error('分析失败，请重试')
  } finally {
    loading.value = false
  }
}

// 计算字数统计
function calculateStats(text) {
  // 总字符数
  const totalChars = text.length
  
  // 中文字符数（Unicode 范围）
  const chineseChars = (text.match(/[\u4e00-\u9fa5]/g) || []).length
  
  // 英文单词数
  const englishWords = (text.match(/[a-zA-Z]+/g) || []).length
  
  // 段落数（按换行符分割）
  const paragraphs = text.split(/\n+/).filter(p => p.trim().length > 0).length
  
  return {
    totalChars,
    chineseChars,
    englishWords,
    paragraphs
  }
}

// 生成评分数据（6个维度）
function generateScores(analysisData) {
  // 根据 AI 分析结果生成分数（0-100）
  const strengths = analysisData.strengths?.length || 0
  const weaknesses = analysisData.weaknesses?.length || 0
  
  // 基础分数
  const baseScore = 70
  
  // 根据优缺点调整分数
  const scoreAdjustment = (strengths - weaknesses) * 3
  
  // 6个维度的分数
  return {
    // 当前分数
    before: [
      Math.min(100, Math.max(40, baseScore + scoreAdjustment + 5)),  // 内容完整性
      Math.min(100, Math.max(40, baseScore + scoreAdjustment)),      // 结构清晰度
      Math.min(100, Math.max(40, baseScore + scoreAdjustment - 2)),  // 表达准确性
      Math.min(100, Math.max(40, baseScore + scoreAdjustment + 3)),  // 逻辑连贯性
      Math.min(100, Math.max(40, baseScore + scoreAdjustment - 5)),  // 重点突出
      Math.min(100, Math.max(40, baseScore + scoreAdjustment + 2))   // 实用价值
    ],
    // 改进后预测分数（根据建议提升）
    after: [
      Math.min(100, baseScore + scoreAdjustment + 5 + 15),  // 内容完整性 +15
      Math.min(100, baseScore + scoreAdjustment + 12),      // 结构清晰度 +12
      Math.min(100, baseScore + scoreAdjustment - 2 + 10),  // 表达准确性 +10
      Math.min(100, baseScore + scoreAdjustment + 3 + 13),  // 逻辑连贯性 +13
      Math.min(100, baseScore + scoreAdjustment - 5 + 18),  // 重点突出 +18
      Math.min(100, baseScore + scoreAdjustment + 2 + 14)   // 实用价值 +14
    ]
  }
}

// 渲染雷达图（按需加载 ECharts，减小非「AI总结」路由的初始加载体积）
async function renderRadarChart(scores) {
  const el = radarChartRef.value
  if (!el) return

  cleanupRadarChartSizing()
  if (radarChart) {
    radarChart.dispose()
    radarChart = null
  }

  await ensureRadarContainerHasLayout(el)

  const echartsNs = await import('echarts')
  const echarts = echartsNs.default ?? echartsNs

  // 判断是否深色主题
  const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const axisNameColor = isDark ? '#aaa' : '#606266'
  const lineColor = isDark ? '#454545' : '#e4e7ed'
  const splitAreaColors = isDark
    ? ['rgba(60,60,60,0.3)', 'rgba(60,60,60,0.5)']
    : ['rgba(245,247,250,0.3)', 'rgba(245,247,250,0.5)']
  const tooltipBg = isDark ? 'rgba(45,45,48,0.95)' : 'rgba(255,255,255,0.95)'
  const tooltipTextColor = isDark ? '#e8e6e3' : '#2d2d2d'
  const tooltipBorderColor = isDark ? '#555' : '#2d2d2d'

  const w = el.clientWidth
  const h = el.clientHeight
  const initOpts =
    w > 0 && h > 0
      ? null
      : { width: Math.max(w, 400), height: Math.max(h, 400) }

  radarChart = initOpts ? echarts.init(el, null, initOpts) : echarts.init(el)
  attachRadarChartSizing(radarChart)
  
  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: tooltipBg,
      borderColor: tooltipBorderColor,
      borderWidth: 1,
      textStyle: { color: tooltipTextColor },
      formatter: function(params) {
        return `${params.name}<br/>${params.seriesName}: ${params.value}分`
      }
    },
    legend: {
      show: false  // 使用自定义图例
    },
    radar: {
      indicator: [
        { name: '内容完整性', max: 100, min: 0 },
        { name: '结构清晰度', max: 100, min: 0 },
        { name: '表达准确性', max: 100, min: 0 },
        { name: '逻辑连贯性', max: 100, min: 0 },
        { name: '重点突出', max: 100, min: 0 },
        { name: '实用价值', max: 100, min: 0 }
      ],
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: axisNameColor,
        fontSize: 12
      },
      splitLine: {
        lineStyle: {
          color: lineColor
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: splitAreaColors
        }
      },
      axisLine: {
        lineStyle: {
          color: lineColor
        }
      }
    },
    series: [
      {
        name: '改进前',
        type: 'radar',
        data: [
          {
            value: scores.before,
            name: '改进前',
            itemStyle: {
              color: '#f5a623'
            },
            areaStyle: {
              color: 'rgba(245, 166, 35, 0.3)'
            },
            lineStyle: {
              width: 2,
              color: '#f5a623'
            }
          }
        ]
      },
      {
        name: '改进后',
        type: 'radar',
        data: [
          {
            value: scores.after,
            name: '改进后',
            itemStyle: {
              color: '#67c23a'
            },
            areaStyle: {
              color: 'rgba(103, 194, 58, 0.2)'
            },
            lineStyle: {
              width: 2,
              type: 'dashed',
              color: '#67c23a'
            }
          }
        ]
      }
    ]
  }
  
  radarChart.setOption(option)
  radarChart.resize()
}

function copyAnalysis() {
  if (!analysisResult.value) return
  
  const text = `
内容总结：
${analysisResult.value.summary}

字数统计：
- 总字符数：${analysisResult.value.totalChars}
- 中文字符：${analysisResult.value.chineseChars}
- 英文单词：${analysisResult.value.englishWords}
- 段落数：${analysisResult.value.paragraphs}

优化建议：
优点：
${analysisResult.value.strengths.map(s => '- ' + s).join('\n')}

不足：
${analysisResult.value.weaknesses.map(w => '- ' + w).join('\n')}

建议：
${analysisResult.value.suggestions.map(t => '- ' + t).join('\n')}
`.trim()
  
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}
</script>

<style scoped>
.ai-summarize-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  background: var(--color-content-bg);
  min-height: 100%;
  color: var(--color-text-primary);
}

/* 页面头部 */
.page-header {
  display: flex;
  margin-bottom: 30px;
  position: relative;
  flex-direction: column;
  align-items: center;
}
.page-title{
}
.page-subtitle{
  text-align: center;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 0;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.back-btn:hover {
  color: var(--color-blue);
}

.page-header h2 {
  font-size: 28px;
  color: var(--color-heading);
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  padding-left: 60px;
}

.page-header p {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
  padding-left: 60px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: var(--color-heading);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-actions {
  display: flex;
  gap: 10px;
}

.input-card,
.result-card,
.empty-card {
  min-height: 100%;
}

.analyze-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
}

/* 分析内容区域 */
.analysis-content {
  max-height: 700px;
  overflow-y: auto;
  padding: 10px;
}

.analysis-section {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-card-border);
}

.analysis-section:last-child {
  border-bottom: none;
}

.section-title {
  font-size: 18px;
  color: var(--color-heading);
  margin: 0 0 15px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.section-title .el-icon {
  font-size: 20px;
  color: var(--color-blue);
}

.section-body {
  font-size: 15px;
  line-height: 1.8;
  color: var(--color-text-secondary);
}

/* 雷达图样式 */
.radar-chart {
  min-width: 240px;
  height: 400px;
  min-height: 400px;
  margin-bottom: 15px;
  margin: 0 180px;
}

.radar-legend {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin-top: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--color-text-secondary);
}

.legend-color {
  width: 20px;
  height: 3px;
  border-radius: 2px;
}

.legend-color.before {
  background: #f5a623;
}

.legend-color.after {
  background: #67c23a;
  border-top: 2px dashed #67c23a;
  height: 0;
}

/* 字数统计网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.stat-item {
  text-align: center;
  padding: 20px 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

/* 优化建议 */
.suggestions {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.suggestion-group {
  padding: 15px;
  border-radius: 8px;
  background: var(--color-content-bg);
  border: 1px solid var(--color-card-border);
}

.suggestion-group.good {
  border-left: 4px solid #67c23a;
}

.suggestion-group.improve {
  border-left: 4px solid #f5a623;
}

.suggestion-group.tips {
  border-left: 4px solid #f56c6c;
}

.suggestion-group h4 {
  font-size: 16px;
  margin: 0 0 10px 0;
  color: var(--color-heading);
  font-weight: 600;
}

.suggestion-group ul {
  margin: 0;
  padding-left: 20px;
}

.suggestion-group li {
  margin: 8px 0;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--color-text-muted);
}

.empty-state h3 {
  font-size: 20px;
  color: var(--color-text-secondary);
  margin: 20px 0 10px 0;
}

.empty-state p {
  font-size: 14px;
  margin: 8px 0;
}

.empty-state .hint {
  color: var(--color-orange);
  font-style: italic;
}

/* 响应式 */
@media (max-width: 768px) {
  .ai-summarize-page {
    padding: 15px;
  }
  
  .page-header h2,
  .page-header p {
    padding-left: 0;
  }
  
  .back-btn {
    position: static;
    margin-bottom: 10px;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>