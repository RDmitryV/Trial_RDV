import { apiClient } from './client'
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '@/types'

export const authApi = {
  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<AuthResponse> {
    const formData = new URLSearchParams()
    formData.append('username', data.email)
    formData.append('password', data.password)

    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data)
    return response.data
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  },

  /**
   * Update user profile
   */
  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await apiClient.put<User>('/api/v1/auth/me', data)
    return response.data
  },
}
