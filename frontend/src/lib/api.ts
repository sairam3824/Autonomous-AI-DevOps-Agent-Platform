import axios from 'axios';
import type {
  AgentRun, AgentRunRequest, AgentMultiRunRequest,
  HealthStatus, InfraGenerateRequest, InfraResponse,
  LoginRequest, LogEntry, Pipeline, PipelineAnalyzeRequest,
  PipelineAnalyzeResponse, PipelineCreate, Project, ProjectCreate,
  RAGQueryRequest, RAGQueryResponse, RAGStats, RegisterRequest, TokenResponse, User,
} from '@/types';
import { API_BASE_URL } from './constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (data: LoginRequest) => api.post<TokenResponse>('/api/v1/auth/login', data),
  register: (data: RegisterRequest) => api.post<TokenResponse>('/api/v1/auth/register', data),
  getMe: () => api.get<User>('/api/v1/auth/me'),
};

export const agentsApi = {
  run: (data: AgentRunRequest) => api.post<AgentRun>('/api/v1/agents/run', data),
  multiRun: (data: AgentMultiRunRequest) => api.post('/api/v1/agents/multi-run', data),
  autoDiagnose: (data: AgentRunRequest) => api.post('/api/v1/agents/auto-diagnose', data),
};

export const projectsApi = {
  list: () => api.get<Project[]>('/api/v1/projects/'),
  get: (id: number) => api.get<Project>(`/api/v1/projects/${id}`),
  create: (data: ProjectCreate) => api.post<Project>('/api/v1/projects/', data),
  update: (id: number, data: Partial<ProjectCreate>) => api.put<Project>(`/api/v1/projects/${id}`, data),
  delete: (id: number) => api.delete(`/api/v1/projects/${id}`),
};

export const pipelinesApi = {
  list: (projectId: number) => api.get<Pipeline[]>(`/api/v1/pipelines/project/${projectId}`),
  create: (data: PipelineCreate) => api.post<Pipeline>('/api/v1/pipelines/', data),
  analyze: (data: PipelineAnalyzeRequest) => api.post<PipelineAnalyzeResponse>('/api/v1/pipelines/analyze', data),
  validate: (data: { yaml_content: string }) => api.post<{ valid: boolean; errors: string[] }>('/api/v1/pipelines/validate', data),
  generate: (data: { requirements: string; platform: string }) => api.post<{ yaml_content: string }>('/api/v1/pipelines/generate', data),
};

export const logsApi = {
  list: (projectId: number) => api.get<LogEntry[]>(`/api/v1/logs/project/${projectId}`),
  create: (data: { source: string; level: string; content: string; project_id: number }) => api.post<LogEntry>('/api/v1/logs/', data),
  upload: (data: { content: string; source: string; project_id: number }) => api.post('/api/v1/logs/upload', data),
  uploadFile: (file: File, projectId: number, source?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('project_id', String(projectId));
    if (source) {
      formData.append('source', source);
    }
    return api.post('/api/v1/logs/upload-file', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  },
  ragQuery: (data: RAGQueryRequest) => api.post<RAGQueryResponse>('/api/v1/logs/rag/query', data),
  ragStats: (projectId: number) => api.get<RAGStats>('/api/v1/logs/rag/stats', { params: { project_id: projectId } }),
  indexDocs: (projectId: number) => api.post('/api/v1/logs/rag/index-docs', null, { params: { project_id: projectId } }),
};

export const infraApi = {
  generate: (data: InfraGenerateRequest) => api.post<InfraResponse>('/api/v1/infra/generate', data),
  execute: (data: { operation: string; config_type: string }) => api.post<InfraResponse>('/api/v1/infra/execute', data),
  status: () => api.get('/api/v1/infra/status'),
};

export const healthApi = {
  check: () => api.get<HealthStatus>('/health'),
};

export default api;
