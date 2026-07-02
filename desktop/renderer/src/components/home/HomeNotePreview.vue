<template>
  <el-main class="center-preview">
    <div v-if="currentNote" class="preview-content">
      <div class="preview-header">
        <h2>{{ currentNote.title }}</h2>
        <div class="preview-actions">
          <el-button
            v-if="!currentNote.is_favorite"
            size="small"
            type="success"
            @click="addToMyNotes(currentNote)"
          >
            加入我的笔记
          </el-button>
          <el-button size="small" @click="editNote(currentNote)">
            <IconEdit :size="16" />
            编辑
          </el-button>
        </div>
      </div>
      <div class="preview-body" v-html="renderedContent"></div>
    </div>
    <div v-else class="empty-preview">
      <IconDocument :size="80" color="#d9d9d9" />
      <h3>选择一个笔记开始预览</h3>
      <p>从左侧选择笔记，或创建新笔记</p>
    </div>
  </el-main>
</template>

<script setup>
import { IconDocument, IconEdit } from '@/components/icons'
import { useHomeInject } from '@/composables/home/useHomeInject'

const { currentNote, renderedContent, addToMyNotes, editNote } = useHomeInject()
</script>
