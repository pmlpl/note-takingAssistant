<template>
  <el-card class="stats-card user-card" shadow="hover">
    <template #header>
      <div class="card-header card-header--fold">
        <span class="card-title">数据统计</span>
        <el-button
          text
          type="primary"
          class="section-toggle-btn"
          @click="visible = !visible"
        >
          <el-icon class="section-toggle-icon" :class="{ 'is-open': visible }">
            <ArrowDown />
          </el-icon>
          <span>展开</span>
        </el-button>
      </div>
    </template>
    <Transition name="section-fold">
      <div v-show="visible" v-loading="loading" class="section-fold-panel">
        <el-alert
          v-if="error && !loading"
          type="error"
          :title="error"
          show-icon
          :closable="false"
          class="section-alert"
        />
        <el-row :gutter="20">
          <el-col :xs="24" :sm="8">
            <div
              class="stat-item stat-notes stat-item--clickable"
              role="button"
              tabindex="0"
              @click="$emit('go-notes')"
              @keydown.enter.prevent="$emit('go-notes')"
            >
              <div class="stat-icon">
                <IconDocument :size="36" color="var(--color-blue)" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ noteCount }}</div>
                <div class="stat-label">
                  <el-tooltip placement="top" :show-after="300">
                    <template #content>
                      当前账号在系统中的笔记总条数。点击前往「我的笔记」列表。
                    </template>
                    <span class="stat-label-inner">笔记数量</span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div
              class="stat-item stat-ai stat-item--clickable"
              role="button"
              tabindex="0"
              @click="$emit('go-home-ai')"
              @keydown.enter.prevent="$emit('go-home-ai')"
            >
              <div class="stat-icon">
                <IconMagic :size="36" color="var(--color-green)" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ aiUsage }}</div>
                <div class="stat-label">
                  <el-tooltip placement="top" :show-after="300">
                    <template #content>
                      AI 生成、摘要、对话等功能的累计调用次数（后端 ai_usage_logs 统计）。点击前往首页 AI 助手。
                    </template>
                    <span class="stat-label-inner">AI使用次数</span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </el-col>
          <el-col :xs="24" :sm="8">
            <div
              class="stat-item stat-active stat-item--clickable"
              role="button"
              tabindex="0"
              @click="$emit('go-history')"
              @keydown.enter.prevent="$emit('go-history')"
            >
              <div class="stat-icon">
                <IconClock :size="36" color="var(--color-warning-deep)" />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatDays(daysActive) }}</div>
                <div class="stat-label">
                  <el-tooltip placement="top" :show-after="300">
                    <template #content>
                      您曾创建过笔记的不同日期天数（按笔记创建日去重）。点击前往历史笔记。
                    </template>
                    <span class="stat-label-inner">活跃天数</span>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </Transition>
  </el-card>
</template>

<script setup>
import { ref } from 'vue'
import { IconDocument, IconMagic, IconClock } from '@/components/icons'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  noteCount: { type: Number, default: 0 },
  aiUsage: { type: Number, default: 0 },
  daysActive: { type: Number, default: 0 },
  defaultVisible: { type: Boolean, default: false }
})

defineEmits(['go-notes', 'go-home-ai', 'go-history'])

const visible = ref(props.defaultVisible)

function formatDays(days) {
  return days > 0 ? `${days}天` : '-'
}
</script>

<style scoped>
.stats-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.user-card :deep(.el-card__body) {
  padding-top: 0;
  padding-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header--fold {
  width: 100%;
}

.section-toggle-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.section-toggle-icon {
  transition: transform 0.36s cubic-bezier(0.33, 1, 0.68, 1);
}

.section-toggle-icon.is-open {
  transform: rotate(-180deg);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.section-fold-panel {
  overflow: hidden;
  padding: 4px 0 20px;
}

.section-alert {
  margin-bottom: 16px;
}

.section-fold-enter-active,
.section-fold-leave-active {
  transition:
    max-height 0.4s cubic-bezier(0.33, 1, 0.68, 1),
    opacity 0.32s ease,
    transform 0.32s ease;
}

.section-fold-enter-from,
.section-fold-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-6px);
}

.section-fold-enter-to,
.section-fold-leave-from {
  max-height: 960px;
  opacity: 1;
  transform: translateY(0);
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 24px 16px;
  border-radius: 8px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, var(--el-fill-color-light) 0%, var(--el-fill-color-blank) 100%);
}

.stat-item--clickable {
  cursor: pointer;
}

.stat-item--clickable:focus {
  outline: 2px solid var(--color-blue);
  outline-offset: 2px;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.stat-notes:hover {
  background: linear-gradient(135deg, rgba(45, 93, 161, 0.08) 0%, var(--el-fill-color-blank) 100%);
}

.stat-ai:hover {
  background: linear-gradient(135deg, rgba(46, 125, 50, 0.07) 0%, var(--el-fill-color-blank) 100%);
}

.stat-active:hover {
  background: linear-gradient(135deg, rgba(180, 83, 9, 0.08) 0%, var(--el-fill-color-blank) 100%);
}

.stat-icon {
  flex-shrink: 0;
  margin-right: 16px;
  padding: 12px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
  line-height: 1;
}

.stat-label {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  font-weight: 500;
}

.stat-label-inner {
  border-bottom: 1px dashed var(--el-text-color-disabled);
  cursor: help;
}

@media (max-width: 768px) {
  .stat-item {
    padding: 20px 12px;
  }

  .stat-value {
    font-size: 28px;
  }
}
</style>
