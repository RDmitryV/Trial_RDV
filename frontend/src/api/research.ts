import { apiClient } from './client'
import type { Research, CreateResearchRequest, PaginatedResponse } from '@/types'

export const researchApi = {
  /**
   * Get all research projects for current user
   */
  async getAll(page: number = 1, pageSize: number = 10): Promise<PaginatedResponse<Research>> {
    const response = await apiClient.get<PaginatedResponse<Research>>('/api/v1/research', {
      params: { page, page_size: pageSize },
    })
    return response.data
  },

  /**
   * Get single research project
   */
  async getById(id: string): Promise<Research> {
    const response = await apiClient.get<Research>(`/api/v1/research/${id}`)
    return response.data
  },

  /**
   * Create new research project
   */
  async create(data: CreateResearchRequest): Promise<Research> {
    const response = await apiClient.post<Research>('/api/v1/research', data)
    return response.data
  },

  /**
   * Update research project
   */
  async update(id: string, data: Partial<CreateResearchRequest>): Promise<Research> {
    const response = await apiClient.put<Research>(`/api/v1/research/${id}`, data)
    return response.data
  },

  /**
   * Delete research project
   */
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/research/${id}`)
  },

  /**
   * Start research analysis
   */
  async startAnalysis(id: string): Promise<Research> {
    const response = await apiClient.post<Research>(`/api/v1/research/${id}/analyze`)
    return response.data
  },
}
