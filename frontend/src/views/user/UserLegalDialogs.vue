<template>
  <el-dialog
    v-model="termsVisible"
    title="用户协议"
    width="min(92vw, 560px)"
    class="legal-dialog"
    destroy-on-close
  >
    <p class="legal-doc-note">以下为通用模板，正式对外服务前请由部署方替换为定稿文本。</p>
    <div class="legal-doc-body">
      <section v-for="(sec, idx) in TERMS_SECTIONS" :key="'term-' + idx" class="legal-doc-section">
        <h4 class="legal-doc-h">{{ sec.h }}</h4>
        <p v-for="(para, pidx) in sec.p" :key="'term-' + idx + '-p-' + pidx" class="legal-doc-p">{{ para }}</p>
      </section>
    </div>
  </el-dialog>

  <el-dialog
    v-model="privacyVisible"
    title="隐私政策"
    width="min(92vw, 560px)"
    class="legal-dialog"
    destroy-on-close
  >
    <p class="legal-doc-note">以下为通用模板，正式对外服务前请由部署方替换为定稿文本。</p>
    <div class="legal-doc-body">
      <section v-for="(sec, idx) in PRIVACY_SECTIONS" :key="'priv-' + idx" class="legal-doc-section">
        <h4 class="legal-doc-h">{{ sec.h }}</h4>
        <p v-for="(para, pidx) in sec.p" :key="'priv-' + idx + '-p-' + pidx" class="legal-doc-p">{{ para }}</p>
      </section>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { TERMS_SECTIONS, PRIVACY_SECTIONS } from '@/constants/userCenterLegal'

const props = defineProps({
  showTerms: { type: Boolean, default: false },
  showPrivacy: { type: Boolean, default: false }
})

const emit = defineEmits(['update:showTerms', 'update:showPrivacy'])

const termsVisible = ref(props.showTerms)
const privacyVisible = ref(props.showPrivacy)

watch(
  () => props.showTerms,
  (val) => {
    termsVisible.value = val
  }
)

watch(
  () => props.showPrivacy,
  (val) => {
    privacyVisible.value = val
  }
)

watch(termsVisible, (val) => {
  emit('update:showTerms', val)
})

watch(privacyVisible, (val) => {
  emit('update:showPrivacy', val)
})
</script>

<style>
.legal-dialog .legal-doc-note {
  margin: 0 0 12px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.legal-dialog .legal-doc-body {
  max-height: min(58vh, 440px);
  overflow-y: auto;
  padding-right: 4px;
}

.legal-dialog .legal-doc-section {
  margin-bottom: 18px;
}

.legal-dialog .legal-doc-section:last-child {
  margin-bottom: 0;
}

.legal-dialog .legal-doc-h {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.legal-dialog .legal-doc-p {
  margin: 0 0 8px;
  font-size: 13px;
  line-height: 1.65;
  color: #606266;
}

.legal-dialog .legal-doc-p:last-child {
  margin-bottom: 0;
}
</style>
