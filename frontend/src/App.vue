<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/layout/AppLayout.vue'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'

const authStore = useAuthStore()
const route = useRoute()

const isAuthPage = computed(() => {
  return route.name === 'login' || route.name === 'register'
})

onMounted(() => {
  // Try to fetch current user if token exists
  if (authStore.isAuthenticated) {
    authStore.fetchCurrentUser().catch(() => {
      // Token might be expired, logout
      authStore.logout()
    })
  }
})
</script>

<template>
  <div id="app">
    <Toast />
    <ConfirmDialog />
    <AppLayout v-if="!isAuthPage && authStore.isAuthenticated">
      <router-view />
    </AppLayout>
    <router-view v-else />
  </div>
</template>

<style scoped>
#app {
  height: 100%;
}
</style>
