export interface User {
  id: number;
  email: string;
  username: string;
  role: 'admin' | 'engineer' | 'viewer';
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface Project {
  id: number;
  name: string;
  description: string | null;
  repo_url: string | null;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  repo_url?: string;
}

export type AgentType = 'infra' | 'pipeline' | 'heal';

export interface AgentRun {
  id: number;
  agent_type: AgentType;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  execution_time_ms: number | null;
  error_message: string | null;
  created_at: string;
}

export interface AgentRunRequest {
  agent_type: AgentType;
  input_data: Record<string, unknown>;
  project_id?: number;
}

export interface AgentMultiRunRequest {
  agents: AgentRunRequest[];
  mode: 'sequential' | 'parallel';
  project_id?: number;
}

export interface Pipeline {
  id: number;
  name: string;
  platform: string;
  yaml_content: string;
  analysis_result: Record<string, unknown> | null;
  project_id: number;
  created_at: string;
  updated_at: string;
}

export interface PipelineCreate {
  name: string;
  platform: string;
  yaml_content: string;
  project_id: number;
}

export interface PipelineAnalyzeRequest {
  yaml_content: string;
  platform: string;
}

export interface PipelineAnalyzeResponse {
  anti_patterns: Array<Record<string, unknown>>;
  suggestions: Array<Record<string, unknown>>;
  optimized_yaml: string | null;
  score: number;
  summary: string;
}

export interface LogEntry {
  id: number;
  source: string;
  level: string;
  content: string;
  metadata: Record<string, unknown> | null;
  project_id: number;
  indexed: boolean;
  created_at: string;
}

export interface RAGQueryRequest {
  question: string;
  k?: number;
  project_id: number;
}

export interface RAGQueryResponse {
  answer: string;
  sources: Array<{ text: string; source: string; relevance_score: number }>;
  confidence: number;
  query: string;
}

export interface RAGStats {
  total_documents: number;
  total_chunks: number;
  index_size_bytes: number;
  embedding_model: string;
}

export interface InfraGenerateRequest {
  config_type: 'docker_compose' | 'kubernetes' | 'terraform';
  app_description: string;
  options?: Record<string, unknown>;
}

export interface InfraResponse {
  success: boolean;
  config_type: string;
  output: string;
  generated_files: Record<string, string> | null;
  metadata: Record<string, unknown> | null;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  services: Record<string, { status: string; [key: string]: unknown }>;
}

export interface WebSocketMessage {
  type: 'started' | 'thinking' | 'action' | 'result' | 'completed' | 'error' | 'final_result';
  agent_type?: string;
  message?: string;
  data?: unknown;
  success?: boolean;
  output?: Record<string, unknown>;
  execution_time_ms?: number;
  timestamp?: number;
}
