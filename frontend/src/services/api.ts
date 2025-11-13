import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  register: (data: { username: string; email?: string; password: string }) =>
    api.post('/api/auth/register', data),

  login: (username: string, password: string) =>
    api.post('/api/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),

  getMe: () => api.get('/api/auth/me'),
}

// Credentials API
export const credentialsApi = {
  // Train credentials
  createTrainCredential: (data: any) => api.post('/api/credentials/train', data),
  getTrainCredentials: () => api.get('/api/credentials/train'),

  // Card credentials
  createCardCredential: (data: any) => api.post('/api/credentials/card', data),
  getCardCredential: () => api.get('/api/credentials/card'),

  // Telegram credentials
  createTelegramCredential: (data: any) => api.post('/api/credentials/telegram', data),
  getTelegramCredential: () => api.get('/api/credentials/telegram'),
}

// Trains API
export const trainsApi = {
  search: (data: any) => api.post('/api/trains/search', data),
  getStations: (trainType: string) => api.get(`/api/trains/stations/${trainType}`),
}

// Reservations API
export const reservationsApi = {
  create: (data: any) => api.post('/api/reservations', data),
  getAll: (limit = 50) => api.get(`/api/reservations?limit=${limit}`),
  getById: (id: number) => api.get(`/api/reservations/${id}`),
  startPolling: (id: number) => api.post(`/api/reservations/${id}/start-polling`),
  stopPolling: (id: number) => api.post(`/api/reservations/${id}/stop-polling`),
  update: (id: number, data: any) => api.patch(`/api/reservations/${id}`, data),
}
