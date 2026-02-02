<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import Menu from 'primevue/menu'
import { ref } from 'vue'

const router = useRouter()
const authStore = useAuthStore()
const menu = ref()

const userMenuItems = ref([
  {
    label: 'Профиль',
    icon: 'pi pi-user',
    command: () => {
      // Navigate to profile
    },
  },
  {
    separator: true,
  },
  {
    label: 'Выход',
    icon: 'pi pi-sign-out',
    command: () => {
      authStore.logout()
      router.push({ name: 'login' })
    },
  },
])

if (authStore.isAdmin) {
  userMenuItems.value.unshift({
    label: 'Админ панель',
    icon: 'pi pi-cog',
    command: () => {
      router.push({ name: 'admin' })
    },
  })
}

const toggleMenu = (event: Event) => {
  menu.value.toggle(event)
}
</script>

<template>
  <div class="surface-0 shadow-2 px-4 py-3 flex align-items-center justify-content-between">
    <div class="flex align-items-center gap-3">
      <router-link to="/" class="text-2xl font-bold text-primary no-underline">
        🤖 Маркетолух
      </router-link>
    </div>

    <div class="flex align-items-center gap-3">
      <Button
        v-if="authStore.isAuthenticated"
        label="Новое исследование"
        icon="pi pi-plus"
        @click="router.push({ name: 'research-create' })"
      />

      <div v-if="authStore.isAuthenticated" class="flex align-items-center gap-2">
        <Avatar
          :label="authStore.user?.full_name?.charAt(0).toUpperCase()"
          class="cursor-pointer"
          size="large"
          shape="circle"
          @click="toggleMenu"
        />
        <Menu ref="menu" :model="userMenuItems" popup />
      </div>
    </div>
  </div>
</template>
