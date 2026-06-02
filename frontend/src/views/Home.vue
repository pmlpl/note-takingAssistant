<template>
  <div class="home-container">
    <el-container class="main-layout">
      <HomeNotesSidebar />
      <HomeNotePreview />
      <HomeAiChatPanel />
    </el-container>
  </div>
</template>

<script setup>
import { provide } from 'vue'
import HomeNotesSidebar from '@/components/home/HomeNotesSidebar.vue'
import HomeNotePreview from '@/components/home/HomeNotePreview.vue'
import HomeAiChatPanel from '@/components/home/HomeAiChatPanel.vue'
import { useHomePage, HOME_PAGE_KEY } from '@/composables/home/useHomePage'
import '@/assets/styles/home.css'

defineOptions({ name: 'Home' })

provide(HOME_PAGE_KEY, useHomePage())
</script>
