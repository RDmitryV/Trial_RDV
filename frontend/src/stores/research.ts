import { defineStore } from 'pinia'
import { ref } from 'vue'
import { researchApi } from '@/api'
import type { Research, CreateResearchRequest } from '@/types'

export const useResearchStore = defineStore('research', () => {
  // State
  const researches = ref<Research[]>([])
  const currentResearch = ref<Research | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(10)

  // Actions
  async function fetchAll(pageNum?: number, size?: number) {
    try {
      loading.value = true
      error.value = null

      if (pageNum) page.value = pageNum
      if (size) pageSize.value = size

      const response = await researchApi.getAll(page.value, pageSize.value)
      researches.value = response.items
      total.value = response.total
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки исследований'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchById(id: string) {
    try {
      loading.value = true
      error.value = null
      currentResearch.value = await researchApi.getById(id)
      return currentResearch.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки исследования'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function create(data: CreateResearchRequest) {
    try {
      loading.value = true
      error.value = null
      const research = await researchApi.create(data)
      researches.value.unshift(research)
      return research
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка создания исследования'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function update(id: string, data: Partial<CreateResearchRequest>) {
    try {
      loading.value = true
      error.value = null
      const updated = await researchApi.update(id, data)

      const index = researches.value.findIndex((r) => r.id === id)
      if (index !== -1) {
        researches.value[index] = updated
      }

      if (currentResearch.value?.id === id) {
        currentResearch.value = updated
      }

      return updated
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка обновления исследования'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function remove(id: string) {
    try {
      loading.value = true
      error.value = null
      await researchApi.delete(id)
      researches.value = researches.value.filter((r) => r.id !== id)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка удаления исследования'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function startAnalysis(id: string) {
    try {
      loading.value = true
      error.value = null
      const updated = await researchApi.startAnalysis(id)

      const index = researches.value.findIndex((r) => r.id === id)
      if (index !== -1) {
        researches.value[index] = updated
      }

      if (currentResearch.value?.id === id) {
        currentResearch.value = updated
      }

      return updated
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка запуска анализа'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearCurrent() {
    currentResearch.value = null
  }

  return {
    // State
    researches,
    currentResearch,
    loading,
    error,
    total,
    page,
    pageSize,
    // Actions
    fetchAll,
    fetchById,
    create,
    update,
    remove,
    startAnalysis,
    clearCurrent,
  }
})
