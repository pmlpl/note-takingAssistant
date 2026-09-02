<template>
  <div
    class="note-card"
    @click="handleClick"
  >
    <!-- Thumbtack -->
    <div class="thumbtack"></div>

    <div class="card-header">
      <h3 class="note-title" :title="note.title">{{ note.title }}</h3>
      <span class="note-date">{{ formatDate(note.created_at) }}</span>
    </div>

    <div class="card-footer">
      <span class="note-tags">
        <span v-for="tag in displayedTags" :key="tag" class="tag">
          {{ tag }}
        </span>
        <span v-if="hasMoreTags" class="tag tag--more">
          +{{ remainingCount }}
        </span>
      </span>
      <div class="card-actions">
        <el-button
          link
          size="small"
          class="action-link"
          @click.stop="emit('edit', note)"
        >
          编辑
        </el-button>
        <el-button
          link
          size="small"
          class="action-link action-link--delete"
          @click.stop="emit('delete', note)"
        >
          删除
        </el-button>
      </div>
    </div>
  </div>
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

const allTags = computed(() => {
  if (!props.note.tags) return []
  return props.note.tags.split(',').filter(tag => tag.trim())
})

const displayedTags = computed(() => allTags.value.slice(0, 3))
const hasMoreTags = computed(() => allTags.value.length > 3)
const remainingCount = computed(() => allTags.value.length - 3)

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
/* ═══ Note Card — Hand-Drawn Wobbly Card ═══ */

.note-card {
  position: relative;
  cursor: pointer;
  background: #ffffff;
  border: 2.5px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-md);
  box-shadow: var(--shadow-hard);
  padding: 20px 18px 16px;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.note-card:hover {
  transform: translateY(-4px) rotate(0.5deg);
  box-shadow: 6px 6px 0px 0px var(--color-pencil);
}

.note-card:active {
  transform: translateY(2px);
  box-shadow: 2px 2px 0px 0px var(--color-pencil);
}

/* ── Red thumbtack ── */
.thumbtack {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%) rotate(5deg);
  width: 18px;
  height: 18px;
  background: var(--color-accent);
  border-radius: 50%;
  box-shadow: 1px 1px 0px rgba(0,0,0,0.3);
  border: 3px solid #fff;
  z-index: 2;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 10px;
}

.note-title {
  font-family: var(--font-heading);
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  color: var(--color-pencil);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* P2 评审 #8：笔记日期 #999(2.85:1) 提至 secondary token（#666，5.74:1 AA） */
.note-date {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

/* ── Tags (hand-drawn style, no Element Plus el-tag) ── */
.note-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  font-family: var(--font-body);
  font-size: 12px;
  padding: 2px 10px;
  background: var(--color-muted);
  border: 2px solid var(--color-pencil);
  border-radius: var(--radius-wobbly-sm);
  color: var(--color-pencil);
  white-space: nowrap;
}

.tag--more {
  background: #fff;
  border-style: dashed;
  color: var(--el-text-color-secondary);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 2px dashed var(--color-muted);
}

.card-actions {
  display: flex;
  gap: 8px;
}

.action-link {
  font-family: var(--font-body) !important;
  font-size: 14px !important;
  /* P3 评审 #11：link 按钮默认仅文字高度（~22px），抬高点击目标至 ≥32px */
  min-height: 32px;
}

.action-link--delete {
  color: var(--color-accent) !important;
}
</style>
