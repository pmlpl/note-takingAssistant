<template>
    <div class="history-notes-page">
      <!-- 页面头部 -->
      <div class="page-header">
        <el-button link @click="goBack" class="back-btn">
          <el-icon size="16"><DArrowLeft /></el-icon>
          <span>返回</span>
        </el-button>
        <h2><IconDocument :size="32" color="var(--color-blue)" /> 历史笔记</h2>
        <p>查看所有笔记，共 {{ totalNotes }} 个</p>
      </div>

      <!-- 搜索和筛选区 -->
      <el-card class="search-card" shadow="hover">
        <div class="search-bar">
          <el-input
            v-model="searchQuery"
            placeholder="按标题搜索笔记..."
            prefix-icon="Search"
            clearable
            class="search-input"
            @input="handleSearch"
          />
          <el-button type="primary" @click="createNewNote">
            <IconPlus :size="18" />
            新建笔记
          </el-button>
        </div>
      </el-card>

      <!-- 笔记列表 -->
      <el-card class="notes-list-card" shadow="hover" v-loading="loading">
        <div v-if="filteredNotes.length > 0" class="notes-grid">
          <div
            v-for="note in filteredNotes"
            :key="note.id"
            class="note-card-item"
            @click="viewNote(note)"
          >
            <div class="note-card-header" @click="viewNote(note)">
              <IconDocument :size="24" color="var(--color-blue)" />
              <h3 class="note-card-title">{{ note.title }}</h3>
            </div>
            <div class="note-card-content">
              {{ truncateContent(note.content) }}
            </div>
            <div class="note-card-footer">
              <span class="note-date">{{ formatDate(note.created_at) }}</span>
              <el-button
                type="danger" 
                link 
                @click.stop="deleteNote(note)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-else class="empty-state">
          <IconDocument :size="80" color="var(--el-text-color-disabled)" />
          <h3>暂无笔记</h3>
          <p>点击右上角"新建笔记"开始创建</p>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination-wrapper">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="total"
            :page-size="pageSize"
            :current-page="page"
            @current-change="handlePageChange"
          />
        </div>
      </el-card>
    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onActivated } from 'vue'
import { useRouter } from 'vue-router'
import { noteApi } from '@/api/note'
import { IconDocument, IconPlus } from '@/components/icons'
import { DArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { MESSAGE_DURATION } from '@/utils/common'
defineOptions({
  name: 'HistoryNotes'
})
const router = useRouter()

const notes = ref([])
const searchQuery = ref('')
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
let searchTimer = null

const totalNotes = computed(() => total.value)

const filteredNotes = computed(() => notes.value)

const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

watch(searchQuery, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadNotes()
  }, 300)
})

onMounted(async () => {
  await loadNotes()
})

onActivated(async () => {
  await loadNotes()
})

async function loadNotes() {
  loading.value = true
  try {
    const res = await noteApi.searchNotes({
      keyword: searchQuery.value,
      page: page.value,
      pageSize,
    })
    notes.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    console.error('加载笔记失败:', error)
    ElMessage.error('加载笔记失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  loadNotes()
}

function handlePageChange(newPage) {
  page.value = newPage
  loadNotes()
}

function goBack() {
  router.back()
}

function createNewNote() {
  router.push('/notes/edit')
}

function viewNote(note) {

  if (!note.id) {
    ElMessage.error('笔记ID无效')
    return
  }

  // 跳转到首页预览，并通过query参数传递笔记ID
  const targetPath = {path: '/home', query: {noteId: String(note.id)}}

  router.push(targetPath).then(() => {
    ElMessage.success('已跳转到笔记预览窗口')
  }).catch(err => {
    console.error('跳转失败:', err)
    ElMessage.error('跳转失败')
  })
}

function editNote(note) {
  router.push(`/notes/edit/${note.id}`)
}

// 删除笔记（从数据库中彻底删除）
async function deleteNote(note) {
  const { ElMessageBox } = await import('element-plus')
  
  try {
    await ElMessageBox.confirm(
      '确定要删除这条笔记吗？此操作不可恢复。',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    
    await noteApi.deleteNote(note.id)
    
    ElMessage.success({ message: '笔记已删除', duration: MESSAGE_DURATION.SHORT })
    
    // 重新加载列表
    await loadAllNotes()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除笔记失败:', error)
      ElMessage.error({ message: '删除失败，请重试', duration: MESSAGE_DURATION.SHORT })
    }
  }
}

// 截断内容显示（支持 Markdown）
function truncateContent(content, maxLength = 150) {
  if (!content) return ''
  // 先移除 Markdown 语法标记，再截取
  const text = content
    .replace(/#{1,6}\s/g, '') // 移除标题标记
    .replace(/\*\*(.+?)\*\*/g, '$1') // 移除粗体
    .replace(/\*(.+?)\*/g, '$1') // 移除斜体
    .replace(/`(.+?)`/g, '$1') // 移除行内代码
    .replace(/\[(.+?)\]\(.+?\)/g, '$1') // 移除链接，保留文本
    .replace(/^[-*+]\s/gm, '') // 移除列表标记
    .replace(/^\d+\.\s/gm, '') // 移除有序列表标记
    .replace(/^>\s/gm, '') // 移除引用标记
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// 格式化日期
function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<style scoped>
.history-notes-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面头部 */
.page-header {
  display: flex;
  margin-bottom: 30px;
  position: relative;
  flex-direction: column;
  align-items: center;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.back-btn:hover {
  color: var(--el-link-color);
}

.page-header h2 {
  font-size: 28px;
  color: var(--el-text-color-primary);
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  padding-left: 60px;
}

.page-header p {
  font-size: 15px;
  color: var(--el-text-color-secondary);
  margin: 0;
  padding-left: 60px;
}

/* 搜索卡片 */
.search-card {
  margin-bottom: 20px;
}

.search-bar {
  display: flex;
  gap: 15px;
  align-items: center;
}

.search-input {
  flex: 1;
}

/* 笔记列表卡片 */
.notes-list-card {
  min-height: 500px;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.note-card-item {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--el-fill-color-blank);
}

.note-card-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
  border-color: var(--color-blue);
}

.note-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.note-card-title {
  font-size: 16px;
  color: var(--el-text-color-primary);
  margin: 0;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.note-card-content {
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin-bottom: 15px;
  height: 60px;
  overflow: hidden;
}

.note-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* P2 评审 #8：历史日期 #909399(2.97:1) 提至 secondary token（#666，AA） */
.note-date {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 20px;
  color: var(--el-text-color-secondary);
}

.empty-state h3 {
  font-size: 20px;
  color: var(--el-text-color-regular);
  margin: 20px 0 10px 0;
}

.empty-state p {
  font-size: 14px;
  margin: 8px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .history-notes-page {
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
  
  .notes-grid {
    grid-template-columns: 1fr;
  }
  
  .search-bar {
    flex-direction: column;
  }
  
  .search-input {
    width: 100%;
  }
}
</style>
