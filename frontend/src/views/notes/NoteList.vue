<template>
  <Layout>
    <div class="note-list-page">
      <!-- 顶部操作区 -->
      <el-card class="top-bar" shadow="never">
        <div class="search-action-group">
          <el-input
            v-model="searchQuery"
            placeholder="按标题搜索笔记..."
            size="large"
            clearable
            class="search-input"
          >
            <template #prefix>
              <IconSearch :size="18" />
            </template>
          </el-input>
          <el-button
            type="primary"
            size="large"
            @click="navigate('/notes/edit')"
            class="create-btn"
          >
            <IconPlus :size="18" color="gray"/>
            创建笔记
          </el-button>
        </div>
      </el-card>

      <!-- 笔记网格区 -->
      <div class="notes-content" v-loading="loading">
        <div v-if="filteredNotes.length > 0" class="notes-grid">
          <NoteCard
            v-for="note in filteredNotes"
            :key="note.id"
            :note="note"
            @click="viewNote(note)"
            @edit="editNote(note)"
            @delete="deleteNote(note)"
          />
        </div>

        <div v-if="filteredNotes.length > 0 && totalPages > 1" class="pagination-wrapper">
          <el-pagination
            background
            layout="prev, pager, next"
            :total="total"
            :page-size="pageSize"
            :current-page="page"
            @current-change="handlePageChange"
          />
        </div>

        <!-- 空状态（勿用 v-else-if 接分页，否则有笔记且仅一页时会误显示） -->
        <el-empty
          v-if="!loading && filteredNotes.length === 0"
          description="暂无笔记"
          :image-size="200"
        >
          <el-button type="primary" @click="navigate('/notes/edit')">
            <IconPlus :size="18" />
            创建第一个笔记
          </el-button>
        </el-empty>
      </div>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, watch, onMounted, onActivated } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useNoteStore } from '@/store'
import { noteApi } from '@/api/note'
import Layout from '@/components/Layout.vue'
import NoteCard from '@/components/NoteCard.vue'
import { IconPlus, IconSearch } from '@/components/icons'
import { MESSAGE_DURATION } from '@/utils/common'
defineOptions({
  name: 'NoteList'
})
const router = useRouter()
const noteStore = useNoteStore()
const searchQuery = ref('')
const notes = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)
let searchTimer = null

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
      isFavorite: true,
    })
    notes.value = res.items || []
    total.value = res.total || 0
  } catch (error) {
    console.error('加载笔记失败:', error)
  } finally {
    loading.value = false
  }
}

function handlePageChange(newPage) {
  page.value = newPage
  loadNotes()
}

function navigate(path) {
  router.push(path)
}

function viewNote(note) {
  // 跳转到首页预览，并通过query参数传递笔记ID
  router.push({ path: '/home', query: { noteId: String(note.id) } })
}

function editNote(note) {
  router.push(`/notes/edit/${note.id}`)
}

async function deleteNote(note) {
  try {
    await noteApi.updateNote(note.id, { is_favorite: false })
    noteStore.deleteNote(note.id)
    ElMessage.success({ message: '已从我的笔记中移除', duration: MESSAGE_DURATION.SHORT })
    await loadNotes()
  } catch (error) {
    console.error('移除笔记失败:', error)
    ElMessage.error({ message: '操作失败，请重试', duration: MESSAGE_DURATION.SHORT })
  }
}

</script>

<style scoped>
.note-list-page {
  min-height: calc(100vh - 60px);
  background: #f5f7fa;
  padding: 20px;
}

/* 顶部操作区 */
.top-bar {
  margin-bottom: 20px;
  border-radius: 12px;
}

.top-bar :deep(.el-card__body) {
  padding: 16px 20px;
}

/* 搜索和操作按钮组 */
.search-action-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 300px;
}

.search-btn {
  flex-shrink: 0;
}

.create-btn {
  flex-shrink: 0;
}

/* 笔记内容区 */
.notes-content {
  min-height: 400px;
}

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 16px 0;
}

/* 网格布局 */
.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .note-list-page {
    padding: 15px;
  }

  .search-action-group {
    flex-direction: column;
    gap: 10px;
  }

  .search-input {
    width: 100%;
    min-width: auto;
  }

  .search-btn,
  .create-btn {
    width: 100%;
  }

  .notes-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
}
</style>

