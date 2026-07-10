<template>
  <el-aside width="240px" class="left-sidebar">
    <div class="sidebar-header">
      <h3><IconNotebook :size="32" />笔记管理</h3>
    </div>
    <!-- 视图切换 -->
    <div class="sidebar-view-toggle">
      <el-radio-group v-model="viewMode" size="small" @change="setViewMode">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="chat">仅聊天</el-radio-button>
        <el-radio-button value="note">仅笔记</el-radio-button>
      </el-radio-group>
    </div>
    <div class="sidebar-actions">
      <el-button type="primary" @click="createNewNote" class="action-btn">
        <IconPlus :size="18" />
        新建笔记
      </el-button>
      <el-button @click="importNote" class="action-btn">
        <IconUpload :size="18" />
        导入笔记
      </el-button>
    </div>
    <div class="notes-list">
      <div class="list-title">最近笔记</div>
      <div v-for="note in recentNotes" :key="note.id" class="note-item" @click="viewNote(note)">
        <IconDocument :size="16" color="#909399" />
        <span class="note-title">{{ note.title }}</span>
      </div>
      <div v-if="recentNotes.length > 10" class="more-notes" @click="goToHistory">
        <span class="more-text">... 更多 ({{ recentNotes.length - 10 }})</span>
      </div>
      <div v-if="recentNotes.length === 0" class="empty-notes">
        <p>暂无笔记</p>
      </div>
    </div>
  </el-aside>
</template>

<script setup>
import { IconPlus, IconUpload, IconDocument, IconNotebook } from '@/components/icons'
import { useHomeInject } from '@/composables/home/useHomeInject'

const { recentNotes, createNewNote, importNote, viewNote, goToHistory, viewMode, setViewMode } = useHomeInject()
</script>
