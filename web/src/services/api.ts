import axios from 'axios';
import { useAuthStore } from '../store/authStore';

export const api = axios.create({
  baseURL: 'http://127.0.0.1:3000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API functions
export const authAPI = {
  login: (email: string, password: string) => 
    api.post('/auth/login', { email, password }),
  
  me: () => api.get('/auth/me'),
  
  register: (userData: any) => 
    api.post('/auth/register', userData),
};

export const generationAPI = {
  generate: (data: any) => 
    api.post('/generation/generate', data),
  
  getJob: (jobId: string) => 
    api.get(`/generation/jobs/${jobId}`),
  
  listJobs: () => 
    api.get('/generation/jobs'),
};

export const bundleAPI = {
  list: (params?: any) => 
    api.get('/bundles/', { params }),
  
  get: (bundleId: string) => 
    api.get(`/bundles/${bundleId}`),
  
  delete: (bundleId: string) => 
    api.delete(`/bundles/${bundleId}`),
};

export const publishAPI = {
  publish: (data: any) => 
    api.post('/publishing/publish', data),
  
  getJob: (jobId: string) => 
    api.get(`/publishing/jobs/${jobId}`),
  
  listJobs: () => 
    api.get('/publishing/jobs'),
  
  testConnection: (platform: string) => 
    api.post(`/publishing/test-connection/${platform}`),
};