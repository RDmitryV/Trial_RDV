<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'

const authStore = useAuthStore()

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
    <router-view />
  </div>
</template>

<style scoped>
#app {
  height: 100%;
}
</style>
