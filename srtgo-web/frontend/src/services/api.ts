import axios, { AxiosResponse } from 'axios';
import {
  User,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserSettings,
  UserSettingsCreate,
  Reservation,
  ReservationCreate,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (data: LoginRequest): Promise<AxiosResponse<TokenResponse>> =>
    api.post('/auth/token', data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      transformRequest: [(data) => {
        const params = new URLSearchParams();
        params.append('username', data.username);
        params.append('password', data.password);
        return params;
      }],
    }),

  register: (data: RegisterRequest): Promise<AxiosResponse<User>> =>
    api.post('/auth/register', data),

  getMe: (): Promise<AxiosResponse<User>> =>
    api.get('/auth/me'),
};

// Settings API
export const settingsAPI = {
  getAll: (): Promise<AxiosResponse<UserSettings[]>> =>
    api.get('/settings'),

  getByRailType: (railType: string): Promise<AxiosResponse<UserSettings>> =>
    api.get(`/settings/${railType}`),

  create: (data: UserSettingsCreate): Promise<AxiosResponse<UserSettings>> =>
    api.post('/settings', data),

  update: (id: number, data: Partial<UserSettingsCreate>): Promise<AxiosResponse<UserSettings>> =>
    api.put(`/settings/${id}`, data),

  delete: (id: number): Promise<AxiosResponse<void>> =>
    api.delete(`/settings/${id}`),
};

// Reservations API
export const reservationsAPI = {
  getAll: (): Promise<AxiosResponse<Reservation[]>> =>
    api.get('/reservations'),

  getById: (id: number): Promise<AxiosResponse<Reservation>> =>
    api.get(`/reservations/${id}`),

  create: (data: ReservationCreate): Promise<AxiosResponse<Reservation>> =>
    api.post('/reservations', data),

  update: (id: number, data: Partial<ReservationCreate>): Promise<AxiosResponse<Reservation>> =>
    api.put(`/reservations/${id}`, data),

  cancel: (id: number): Promise<AxiosResponse<void>> =>
    api.delete(`/reservations/${id}`),
};

// Utility API
export const utilityAPI = {
  getStations: (railType?: string): Promise<AxiosResponse<string[]>> =>
    api.get(`/utils/stations${railType ? `?rail_type=${railType}` : ''}`),

  getPassengerTypes: (): Promise<AxiosResponse<{ key: string; label: string }[]>> =>
    api.get('/utils/passenger-types'),

  getSeatTypes: (): Promise<AxiosResponse<{ key: string; label: string }[]>> =>
    api.get('/utils/seat-types'),

  getTimeChoices: (): Promise<AxiosResponse<{ value: string; label: string }[]>> =>
    api.get('/utils/time-choices'),

  searchTrains: (params: {
    rail_type: string;
    departure: string;
    arrival: string;
    date: string;
    time: string;
  }) => api.post('/utils/search-trains', params),
};

export default api;