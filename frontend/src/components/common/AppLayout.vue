<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Menu from 'primevue/menu'
import Avatar from 'primevue/avatar'
import Button from 'primevue/button'

const router = useRouter()
const authStore = useAuthStore()
const sidebarVisible = ref(true)

const menuItems = ref([
  {
    label: 'Главная',
    icon: 'pi pi-home',
    command: () => router.push({ name: 'dashboard' })
  },
  {
    label: 'Исследования',
    icon: 'pi pi-chart-line',
    command: () => router.push({ name: 'dashboard' })
  },
  {
    label: 'Аналитика',
    icon: 'pi pi-chart-bar',
    disabled: true
  },
  {
    separator: true
  },
  {
    label: 'Настройки',
    icon: 'pi pi-cog',
    disabled: true
  },
  {
    label: 'Выйти',
    icon: 'pi pi-sign-out',
    command: () => {
      authStore.logout()
      router.push({ name: 'login' })
    }
  }
])

const toggleSidebar = () => {
  sidebarVisible.value = !sidebarVisible.value
}

const getUserInitials = () => {
  return authStore.user?.full_name?.charAt(0).toUpperCase() || 'U'
}
</script>

<template>
  <div class="app-layout">
    <!-- Top Header -->
    <div class="app-header">
      <div class="header-left">
        <Button
          icon="pi pi-bars"
          text
          rounded
          @click="toggleSidebar"
          class="menu-toggle"
        />
        <h2 class="app-title">🤖 Маркетолух</h2>
      </div>
      <div class="header-right">
        <Button
          label="Новое исследование"
          icon="pi pi-plus"
          @click="router.push({ name: 'research-create' })"
        />
        <Avatar
          :label="getUserInitials()"
          shape="circle"
          size="large"
          class="user-avatar"
        />
      </div>
    </div>

    <div class="app-body">
      <!-- Sidebar -->
      <aside v-if="sidebarVisible" class="app-sidebar">
        <div class="sidebar-content">
          <div class="user-info">
            <Avatar
              :label="getUserInitials()"
              size="xlarge"
              shape="circle"
            />
            <h3>{{ authStore.user?.full_name }}</h3>
            <p class="user-email">{{ authStore.user?.email }}</p>
            <span v-if="authStore.user?.is_admin" class="admin-badge">Администратор</span>
          </div>
          <Menu :model="menuItems" class="sidebar-menu" />
        </div>
      </aside>

      <!-- Main Content -->
      <main class="app-content" :class="{ 'full-width': !sidebarVisible }">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f8f9fa;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.app-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.menu-toggle {
  font-size: 1.25rem;
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
  transition: all 0.3s ease;
}

.sidebar-content {
  padding: 2rem 1rem;
}

.user-info {
  text-align: center;
  padding: 1rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid #e5e7eb;
}

.user-info h3 {
  margin: 1rem 0 0.25rem;
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.user-email {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.admin-badge {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.25rem 0.75rem;
  background: #dbeafe;
  color: #1e40af;
  border-radius: 1rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.sidebar-menu {
  border: none;
  width: 100%;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  transition: all 0.3s ease;
}

.app-content.full-width {
  width: 100%;
}
</style>
