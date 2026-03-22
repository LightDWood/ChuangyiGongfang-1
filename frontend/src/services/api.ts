import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  login: async (username: string, password: string) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  register: async (username: string, email: string, password: string) => {
    const response = await api.post('/auth/register', {
      username,
      email,
      password,
    });
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },

  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  refresh: async () => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },
};

export const sessionService = {
  list: async () => {
    const response = await api.get('/sessions');
    return response.data;
  },

  create: async (title: string) => {
    const response = await api.post('/sessions', { title });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/sessions/${id}`);
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/sessions/${id}`);
    return response.data;
  },
};

export const messageService = {
  list: async (sessionId: string) => {
    const response = await api.get(`/sessions/${sessionId}/messages`);
    return response.data;
  },

  send: async (sessionId: string, content: string) => {
    const response = await api.post(`/sessions/${sessionId}/messages`, {
      content,
    });
    return response.data;
  },

  stream: (sessionId: string, content: string) => {
    const token = localStorage.getItem('access_token');
    return new EventSource(
      `/api/sessions/${sessionId}/stream?content=${encodeURIComponent(content)}&token=${token}`
    );
  },
};

export const artifactService = {
  list: async (sessionId: string) => {
    const response = await api.get(`/sessions/${sessionId}/artifacts`);
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/artifacts/${id}`);
    return response.data;
  },

  update: async (id: string, content: string) => {
    const response = await api.put(`/artifacts/${id}`, { content });
    return response.data;
  },

  delete: async (id: string) => {
    const response = await api.delete(`/artifacts/${id}`);
    return response.data;
  },
};

export default api;
