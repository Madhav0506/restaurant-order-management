import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          
          localStorage.setItem('access_token', data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.clear();
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username, password) => 
    api.post('/auth/login/', { username, password }),
  
  register: (userData) => 
    api.post('/auth/register/', userData),
};

// Service Request API
export const serviceRequestAPI = {
  getAll: () => api.get('/requests/'),
  
  getPending: () => api.get('/requests/pending_requests/'),
  
  create: (requestData) => api.post('/requests/', requestData),
  
  updateStatus: (id, status) => 
    api.patch(`/requests/${id}/update_status/`, { status }),
  
  getById: (id) => api.get(`/requests/${id}/`),
};

// Notification API
export const notificationAPI = {
  getAll: () => api.get('/notifications/'),
  
  markRead: (id) => api.patch(`/notifications/${id}/mark_read/`),
  
  markAllRead: () => api.post('/notifications/mark_all_read/'),
  
  getUnreadCount: () => api.get('/notifications/unread_count/'),
};

// Table API
export const tableAPI = {
  getAll: () => api.get('/tables/'),
  
  toggleOccupancy: (id) => api.post(`/tables/${id}/toggle_occupancy/`),
};

// Device API
export const deviceAPI = {
  register: (deviceData) => api.post('/devices/register_device/', deviceData),
  
  getAll: () => api.get('/devices/'),
};

export default api;
