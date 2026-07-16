/**
 * API service with Axios instance and JWT interceptors.
 */

import axios from 'axios';
import { getToken, getRefreshToken, setToken, removeToken } from './auth';

const API_BASE_URL = '/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) {
          removeToken();
          window.location.href = '/login';
          return Promise.reject(error);
        }

        const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        setToken(access, refreshToken);
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (refreshError) {
        removeToken();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login/', { username, password }),

  register: (username, email, password, passwordConfirm) =>
    api.post('/auth/register/', {
      username,
      email,
      password,
      password_confirm: passwordConfirm,
    }),

  getProfile: () => api.get('/auth/profile/'),
};

// Query API
export const queryAPI = {
  submit: (data) => api.post('/query/submit/', data),

  getHistory: (page = 1) => api.get(`/query/history/?page=${page}`),

  getDetail: (id) => api.get(`/query/${id}/`),

  getStats: () => api.get('/query/stats/'),
};

// Feedback API
export const feedbackAPI = {
  submit: (data) => api.post('/feedback/', data),
};

// Health API
export const healthAPI = {
  check: () => api.get('/health/'),
};

export default api;
