
import axios from 'axios';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Helper to get full API URL
export const getFullApiUrl = (path: string): string => {
  // Make sure path starts with a slash
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Types
export interface APIResponse<T = any> {
  success: boolean;
  message?: string;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

export interface SystemStatus {
  data_files: { [key: string]: boolean };
  store_templates: string[];
  lob_status: { [key: string]: boolean };
  system_health: string;
  active_jobs: number;
  project_root: string;
  directories: {
    data: string;
    output: string;
    logs: string;
  };
  disk_usage: {
    output_mb: number;
    logs_mb: number;
    data_mb: number;
  };
  jobs: {
    total: number;
    running: number;
    completed: number;
    failed: number;
  };
}

export interface OptimizationJob {
  job_id: string;
  job_type: string;
  parameters: any;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  has_result: boolean;
  has_error: boolean;
  summary?: {
    products_placed?: number;
    products_rejected?: number;
    utilization?: number;
    warnings_count?: number;
  };
}

export interface ValidParameters {
  lobs: string[];
  categories: string[];
  store_types: string[];
  strategies: string[];
  strategy_descriptions: { [key: string]: string };
}

// API Functions
export const apiService = {
  // Health and Status
  async getHealth(): Promise<APIResponse> {
    const response = await api.get('/api/health');
    return response.data;
  },

  async getSystemStatus(): Promise<APIResponse<SystemStatus>> {
    const response = await api.get('/api/system/info');
    return response.data;
  },

  async getValidParameters(): Promise<APIResponse<ValidParameters>> {
    const response = await api.get('/api/validate/parameters');
    return response.data;
  },

  // Optimization Endpoints
  async startCohortOptimization(lob: string, storeType: string): Promise<APIResponse<{ job_id: string }>> {
    const response = await api.post('/api/optimize/cohort', {
      lob,
      store_type: storeType
    });
    return response.data;
  },

  async startLOBOptimization(lob: string, storeType: string, strategy: string): Promise<APIResponse<{ job_id: string }>> {
    const response = await api.post('/api/optimize/lob', {
      lob,
      store_type: storeType,
      strategy
    });
    return response.data;
  },

  async startCategoryOptimization(category: string, storeType: string, strategy: string): Promise<APIResponse<{ job_id: string }>> {
    const response = await api.post('/api/optimize/category', {
      category,
      store_type: storeType,
      strategy
    });
    return response.data;
  },

  async startFullStoreOptimization(storeType: string, strategy: string): Promise<APIResponse<{ job_id: string }>> {
    const response = await api.post('/api/optimize/full-store', {
      store_type: storeType,
      strategy
    });
    return response.data;
  },

  // Job Management
  async getJobs(): Promise<APIResponse<{ jobs: OptimizationJob[] }>> {
    const response = await api.get('/api/jobs');
    return response.data;
  },

  async getJobDetails(jobId: string): Promise<APIResponse<any>> {
    const response = await api.get(`/api/jobs/${jobId}`);
    return response.data;
  },

  async cancelJob(jobId: string): Promise<APIResponse> {
    const response = await api.delete(`/api/jobs/${jobId}`);
    return response.data;
  },

  // Results Management
  async getResults(filters?: { type?: string; status?: string; limit?: number }): Promise<APIResponse<{ results: OptimizationJob[] }>> {
    const params = new URLSearchParams();
    if (filters?.type) params.append('type', filters.type);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    
    const response = await api.get(`/api/results/list?${params.toString()}`);
    return response.data;
  },

  async getResultDetails(jobId: string): Promise<APIResponse<any>> {
    const response = await api.get(`/api/results/${jobId}`);
    return response.data;
  },

  async deleteResult(jobId: string): Promise<APIResponse> {
    const response = await api.delete(`/api/results/${jobId}`);
    return response.data;
  },

  async downloadResultFile(jobId: string, fileType: string): Promise<Blob> {
    const response = await api.get(`/api/results/${jobId}/download/${fileType}`, {
      responseType: 'blob'
    });
    return response.data;
  },

  // File Management
  async getOutputFiles(pattern?: string): Promise<APIResponse<{ files: any[] }>> {
    const params = pattern ? `?pattern=${encodeURIComponent(pattern)}` : '';
    const response = await api.get(`/api/files/list${params}`);
    return response.data;
  },

  async deleteFile(filename: string): Promise<APIResponse> {
    return api.delete(`/api/files/${filename}`);
  },

  // Store Template Management
  async getStoreTemplates(): Promise<APIResponse<{ stores: any[], total_stores: number }>> {
    return api.get('/api/stores/templates');
  },

  async getStoreWalls(storeName: string): Promise<APIResponse<any>> {
    return api.get(`/api/stores/${encodeURIComponent(storeName)}/walls`);
  },

  async startStoreOptimization(storeName: string, params: {
    optimization_type?: string;
    selected_lobs?: string[];
    additional_params?: any;
  }): Promise<APIResponse<{ job_id: string }>> {
    return api.post(`/api/stores/${encodeURIComponent(storeName)}/optimize`, params);
  },

  async generatePlanogram(storeName: string, selectedAccessories: string[]): Promise<APIResponse<{ job_id: string }>> {
    return api.post(`/api/stores/${encodeURIComponent(storeName)}/generate-planograms`, {
        selected_accessories: selectedAccessories,
    });
  },
};

export default api;
