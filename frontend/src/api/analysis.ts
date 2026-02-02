import { apiClient } from './client'
import type {
  AnalysisResult,
  TrendAnalysisRequest,
  RegionalAnalysisRequest,
  CompetitiveAnalysisRequest,
} from '@/types'

export const analysisApi = {
  /**
   * Get all analysis results for a research project
   */
  async getResults(researchId: string): Promise<AnalysisResult[]> {
    const response = await apiClient.get<AnalysisResult[]>(
      `/api/v1/analysis/results/${researchId}`
    )
    return response.data
  },

  /**
   * Perform trend analysis
   */
  async analyzeTrends(data: TrendAnalysisRequest): Promise<Record<string, any>> {
    const response = await apiClient.post<Record<string, any>>('/api/v1/analysis/trends', data)
    return response.data
  },

  /**
   * Perform regional analysis
   */
  async analyzeRegional(data: RegionalAnalysisRequest): Promise<Record<string, any>> {
    const response = await apiClient.post<Record<string, any>>('/api/v1/analysis/regional', data)
    return response.data
  },

  /**
   * Perform competitive analysis
   */
  async analyzeCompetitive(data: CompetitiveAnalysisRequest): Promise<Record<string, any>> {
    const response = await apiClient.post<Record<string, any>>(
      '/api/v1/analysis/competitive',
      data
    )
    return response.data
  },
}
