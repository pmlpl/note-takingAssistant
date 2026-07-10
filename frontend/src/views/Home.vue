<template>
  <div class="home-container" :class="`view-mode-${viewMode}`">
    <el-container class="main-layout">
      <HomeNotesSidebar />
      <HomeNotePreview />
      <HomeAiChatPanel />
    </el-container>
  </div>
</template>

<script setup>
import { provide, computed } from 'vue'
import HomeNotesSidebar from '@/components/home/HomeNotesSidebar.vue'
import HomeNotePreview from '@/components/home/HomeNotePreview.vue'
import HomeAiChatPanel from '@/components/home/HomeAiChatPanel.vue'
import { useHomePage, HOME_PAGE_KEY } from '@/composables/home/useHomePage'
import '@/assets/styles/home.css'

defineOptions({ name: 'Home' })

const homePage = useHomePage()
const viewMode = computed(() => homePage.viewMode.value)

provide(HOME_PAGE_KEY, homePage)
</script>
