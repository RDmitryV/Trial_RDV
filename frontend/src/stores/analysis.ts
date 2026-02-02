import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analysisApi } from '@/api'
import type { AnalysisResult } from '@/types'

export const useAnalysisStore = defineStore('analysis', () => {
  // State
  const results = ref<AnalysisResult[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchResults(researchId: string) {
    try {
      loading.value = true
      error.value = null
      results.value = await analysisApi.getResults(researchId)
      return results.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Ошибка загрузки результатов'
      throw err
    } finally {
      loading.value = false
    }
  }

  function clearResults() {
    results.value = []
  }

  return {
    // State
    results,
    loading,
    error,
    // Actions
    fetchResults,
    clearResults,
  }
})
