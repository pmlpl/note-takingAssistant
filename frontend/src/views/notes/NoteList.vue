<template>
  <Layout>
    <div class="note-list-page">
      <!-- 顶部操作区 -->
      <el-card class="top-bar" shadow="never">
        <div class="search-action-group">
          <el-input
            v-model="searchQuery"
            placeholder="搜索笔记..."
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
      <div class="notes-content">
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

        <!-- 空状态 -->
        <el-empty
          v-else
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNoteStore } from '@/store'
import { noteApi } from '@/api/note'
import Layout from '@/components/Layout.vue'
import NoteCard from '@/components/NoteCard.vue'
import { IconPlus, IconSearch } from '@/components/icons'
import { ElMessage } from 'element-plus'
import { MESSAGE_DURATION } from '@/utils/common'
defineOptions({
  name: 'NoteList'
})
const router = useRouter()
const noteStore = useNoteStore()
const searchQuery = ref('')

const notes = computed(() => noteStore.notes)
const filteredNotes = computed(() => {
  // 只显示已加入"我的笔记"的笔记
  const favoriteNotes = notes.value.filter(note => note.is_favorite)
  
  if (!searchQuery.value) return favoriteNotes
  const query = searchQuery.value.toLowerCase()
  return favoriteNotes.filter(note =>
    note.title.toLowerCase().includes(query) ||
    note.content.toLowerCase().includes(query)
  )
})

onMounted(async () => {
  await loadNotes()
})

async function loadNotes() {
  try {
    const data = await noteApi.getNotes()
    noteStore.setNotes(data)
  } catch (error) {
    console.error('加载笔记失败:', error)
  }
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
    // 将 is_favorite 设置为 false，从“我的笔记”中移除
    await noteApi.updateNote(note.id, { is_favorite: false })
    
    // 从 store 中移除
    noteStore.deleteNote(note.id)
    
    ElMessage.success({ message: '已从我的笔记中移除', duration: MESSAGE_DURATION.SHORT })
    
    // 重新加载列表
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

