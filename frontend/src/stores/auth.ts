import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import type { User, LoginRequest, RegisterRequest } from '@/types'

const TOKEN_KEY = 'marketoluh_token'
const USER_KEY = 'marketoluh_user'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(
    localStorage.getItem(USER_KEY) ? JSON.parse(localStorage.getItem(USER_KEY)!) : null
  )
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin || false)

  // Actions
  async function login(credentials: LoginRequest) {
    try {
      loading.value = true
      error.value = null
      const response = await authApi.login(credentials)

      token.value = response.access_token
      user.value = response.user

      localStorage.setItem(TOKEN_KEY, response.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(response.user))

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка входа'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest) {
    try {
      loading.value = true
      error.value = null
      const response = await authApi.register(data)

      token.value = response.access_token
      user.value = response.user

      localStorage.setItem(TOKEN_KEY, response.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(response.user))

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка регистрации'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentUser() {
    try {
      loading.value = true
      const userData = await authApi.getCurrentUser()
      user.value = userData
      localStorage.setItem(USER_KEY, JSON.stringify(userData))
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки профиля'
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return {
    // State
    token,
    user,
    loading,
    error,
    // Getters
    isAuthenticated,
    isAdmin,
    // Actions
    login,
    register,
    fetchCurrentUser,
    logout,
  }
})
