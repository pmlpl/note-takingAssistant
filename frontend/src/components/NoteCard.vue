<template>
  <el-card 
    class="note-card" 
    hover
    @click="handleClick"
  >
    <div class="card-header">
      <h3 class="note-title"  :title="note.title">{{ note.title }}</h3>
      <span class="note-date">{{ formatDate(note.created_at) }}</span>
    </div>
    <div class="card-footer">
      <span class="note-tags">
        <el-tag v-for="tag in displayedTags" :key="tag" size="small">
          {{ tag }}
        </el-tag>
        <el-tag v-if="hasMoreTags" size="small" type="info" effect="plain">
          +{{ remainingCount }}
        </el-tag>
      </span>
      <div class="card-actions">
        <el-button 
          link 
          size="small" 
          @click.stop="emit('edit', note)"
        >编辑</el-button>
        <el-button 
          link 
          size="small" 
          @click.stop="emit('delete', note)"
          class="delete-btn"
        >删除</el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  note: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click', 'edit', 'delete'])

// 获取所有标签
const allTags = computed(() => {
  if (!props.note.tags) return []
  return props.note.tags.split(',').filter(tag => tag.trim())
})

// 显示的标签（最多3个）
const displayedTags = computed(() => {
  return allTags.value.slice(0, 3)
})

// 是否有更多标签
const hasMoreTags = computed(() => {
  return allTags.value.length > 3
})

// 剩余标签数量
const remainingCount = computed(() => {
  return allTags.value.length - 3
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

function handleClick() {
  emit('click')
}
</script>

<style scoped>
.note-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.note-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
  gap: 10px;
}

.note-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #303133;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note-date {
  font-size: 12px;
  color: #909399;
}

/* Markdown 渲染样式 */
.note-content :deep(h1),
.note-content :deep(h2),
.note-content :deep(h3),
.note-content :deep(h4),
.note-content :deep(h5),
.note-content :deep(h6) {
  margin: 8px 0;
  font-weight: 600;
  line-height: 1.4;
}

.note-content :deep(h1) { font-size: 1.5em; }
.note-content :deep(h2) { font-size: 1.3em; }
.note-content :deep(h3) { font-size: 1.1em; }

.note-content :deep(p) {
  margin: 4px 0;
}

.note-content :deep(code) {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.note-content :deep(pre) {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
}

.note-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.note-content :deep(blockquote) {
  border-left: 3px solid #409eff;
  padding-left: 12px;
  margin: 8px 0;
  color: #606266;
}

.note-content :deep(ul),
.note-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.note-content :deep(li) {
  margin: 4px 0;
}

.note-content :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.note-content :deep(a:hover) {
  text-decoration: underline;
}

.note-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.note-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}

.note-content :deep(th),
.note-content :deep(td) {
  border: 1px solid #e4e7ed;
  padding: 6px 10px;
  text-align: left;
}

.note-content :deep(th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
}

.note-tags {
  display: flex;
  gap: 5px;
}

.card-actions {
  display: flex;
  gap: 10px;
}

.delete-btn {
  color: #f56c6c;
}
</style>