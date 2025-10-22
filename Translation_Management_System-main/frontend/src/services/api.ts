import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { useStore } from '../store/useStore';

const API_URL = import.meta.env.VITE_API_URL || '';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = useStore.getState().token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          useStore.getState().logout();
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication endpoints
  async login(email: string, password: string) {
    const response = await this.api.post('/auth/login', { email, password });
    return response.data;
  }

  async register(userData: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
    role?: string;
  }) {
    const response = await this.api.post('/auth/register', userData);
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.api.get('/auth/me');
    return response.data;
  }

  async getLocales() {
    const response = await this.api.get('/locales');
    return response.data;
  }

  // Projects endpoints
  async getProjects() {
    const response = await this.api.get('/projects');
    return response.data;
  }

  async getProject(projectId: string) {
    const response = await this.api.get(`/projects/${projectId}`);
    return response.data;
  }

  async createProject(projectData: any) {
    const response = await this.api.post('/projects', projectData);
    return response.data;
  }

  async updateProject(projectId: string, updates: any) {
    const response = await this.api.put(`/projects/${projectId}`, updates);
    return response.data;
  }

  async deleteProject(projectId: string) {
    const response = await this.api.delete(`/projects/${projectId}`);
    return response.data;
  }

  // Segments endpoints
  async getProjectSegments(projectId: string) {
    const response = await this.api.get(`/projects/${projectId}/segments`);
    return response.data;
  }

  async updateSegment(projectId: string, segmentId: string, updates: any) {
    const response = await this.api.post(
      `/projects/${projectId}/segments/${segmentId}`,
      updates
    );
    return response.data;
  }

  // Translation endpoints
  async translateText(data: {
    source_text: string;
    source_lang: string;
    target_lang: string;
    context?: string;
    provider?: string;
  }) {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined) {
        formData.append(key, value);
      }
    });

    const response = await this.api.post('/translate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async estimateQuality(data: {
    source_text: string;
    translated_text: string;
    source_lang: string;
    target_lang: string;
  }) {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      formData.append(key, value);
    });

    const response = await this.api.post('/quality-estimate', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async suggestImprovements(data: {
    source_text: string;
    translated_text: string;
    context?: string;
  }) {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined) {
        formData.append(key, value);
      }
    });

    const response = await this.api.post('/suggest-improvements', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // File upload
  async uploadFile(file: File, projectId: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', projectId);

    const response = await this.api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Dashboard endpoints
  async getDashboardSummary() {
    const response = await this.api.get('/dashboard/summary');
    return response.data;
  }

  async getAnalyticsSummary() {
    const response = await this.api.get('/analytics/summary');
    return response.data;
  }

  async getAnalyticsOverview() {
    const response = await this.api.get('/analytics/overview');
    return response.data;
  }

  // Translation studio
  async getStudioSnapshot(projectId: string, targetLocale: string) {
    const response = await this.api.get(
      `/translation-studio/${projectId}?target_locale=${targetLocale}`
    );
    return response.data;
  }

  // Connectors
  async getConnectors() {
    const response = await this.api.get('/connectors');
    return response.data;
  }

  async createConnector(connectorData: any) {
    const response = await this.api.post('/connectors', connectorData);
    return response.data;
  }

  // Vendors
  async getVendors() {
    const response = await this.api.get('/vendors');
    return response.data;
  }

  // Translation memory
  async addTranslationMemory(data: {
    source_locale: string;
    target_locale: string;
    source_text: string;
    translated_text: string;
  }) {
    const response = await this.api.post('/translation-memory', data);
    return response.data;
  }

  // Jobs
  async getJobs() {
    const response = await this.api.get('/jobs');
    return response.data;
  }

  async completeJobStep(jobId: string, stepName: string, data: any) {
    const response = await this.api.post(
      `/jobs/${jobId}/steps/${stepName}/complete`,
      data
    );
    return response.data;
  }

  async submitQualityReport(jobId: string, report: any) {
    const response = await this.api.post(`/jobs/${jobId}/quality`, report);
    return response.data;
  }

  // Health check
  async healthCheck() {
    const response = await this.api.get('/health');
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;
