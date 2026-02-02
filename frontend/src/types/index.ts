// User types
export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  full_name: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// Research types
export interface Research {
  id: string
  title: string
  description: string
  product_description: string
  industry: string
  region: string
  status: ResearchStatus
  created_at: string
  updated_at: string
  user_id: string
}

export const ResearchStatus = {
  DRAFT: 'draft',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed'
} as const

export type ResearchStatus = typeof ResearchStatus[keyof typeof ResearchStatus]

export interface CreateResearchRequest {
  title: string
  description: string
  product_description: string
  industry: string
  region: string
  additional_params?: Record<string, any>
}

// Analysis types
export interface AnalysisResult {
  id: string
  research_id: string
  analysis_type: AnalysisType
  title: string
  summary: string
  results: Record<string, any>
  confidence_score?: number
  created_at: string
}

export const AnalysisType = {
  TREND: 'trend',
  REGIONAL: 'regional',
  COMPETITIVE: 'competitive',
  MARKET: 'market'
} as const

export type AnalysisType = typeof AnalysisType[keyof typeof AnalysisType]

export interface TrendAnalysisRequest {
  research_id: string
  industry: string
}

export interface RegionalAnalysisRequest {
  research_id: string
  region_name: string
  industry: string
}

export interface CompetitiveAnalysisRequest {
  research_id: string
  competitor_data: CompetitorData[]
  our_product: ProductData
}

export interface CompetitorData {
  name: string
  description: string
  market_share?: number
  website?: string
}

export interface ProductData {
  name: string
  description: string
  features: string[]
}

// Common types
export interface ApiError {
  detail: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}
