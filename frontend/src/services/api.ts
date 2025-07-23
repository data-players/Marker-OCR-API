import axios, { AxiosInstance, AxiosResponse } from 'axios'

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 60000, // Increased from 30s to 60s for general requests
  headers: {
    'Content-Type': 'application/json',
  },
})

// Create special instance for long-running operations (document processing)
const longRunningApiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 300000, // 5 minutes for document processing (model download + processing)
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth headers
apiClient.interceptors.request.use(
  (config) => {
    // Add API key if available
    const apiKey = localStorage.getItem('api_key')
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey
    }
    
    // Add request ID for tracing
    config.headers['X-Request-ID'] = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Same interceptors for long-running client
longRunningApiClient.interceptors.request.use(
  (config) => {
    // Add API key if available
    const apiKey = localStorage.getItem('api_key')
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey
    }
    
    // Add request ID for tracing
    config.headers['X-Request-ID'] = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    // Log error for debugging
    console.error('API Error:', error.response?.data || error.message)
    
    // Handle common error cases
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('api_key')
      window.location.href = '/'
    }
    
    return Promise.reject(error)
  }
)

// Same response interceptor for long-running client
longRunningApiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    // Log error for debugging
    console.error('Long-running API Error:', error.response?.data || error.message)
    
    // Handle common error cases
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('api_key')
      window.location.href = '/'
    }
    
    return Promise.reject(error)
  }
)

// Type definitions
export interface FileUploadResponse {
  file_id: string
  filename: string
  size: number
  upload_timestamp: string
}

export interface ProcessingOptions {
  processing_option: 'fast' | 'accurate' | 'ocr_only'
  output_format: 'json' | 'markdown' | 'both'
  force_ocr: boolean
  extract_images: boolean
  extract_tables: boolean
  language?: string
}

export interface ProcessResponse {
  job_id: string
  status: string
  estimated_time?: number
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  updated_at: string
  progress?: number
  result?: any
  error_message?: string
}

export interface HealthStatus {
  status: string
  version: string
  timestamp: string
  services: Record<string, string>
}

// API service functions
export const apiService = {
  // Health check
  async checkHealth(): Promise<HealthStatus> {
    const response = await apiClient.get<HealthStatus>('/health')
    return response.data
  },

  // File operations
  async uploadFile(file: File): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await apiClient.post<FileUploadResponse>(
      '/documents/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  // Document processing
  async processDocument(
    fileId: string,
    options: Partial<ProcessingOptions> = {}
  ): Promise<ProcessResponse> {
    const formData = new FormData()
    formData.append('file_id', fileId)
    formData.append('processing_option', options.processing_option || 'accurate')
    formData.append('output_format', options.output_format || 'both')
    formData.append('force_ocr', String(options.force_ocr || false))
    formData.append('extract_images', String(options.extract_images !== false))
    formData.append('extract_tables', String(options.extract_tables !== false))
    
    if (options.language) {
      formData.append('language', options.language)
    }

    // Use long-running client for document processing to handle model downloads
    const response = await longRunningApiClient.post<ProcessResponse>(
      '/documents/process',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    return response.data
  },

  // Job status
  async getJobStatus(jobId: string): Promise<JobStatus> {
    const response = await apiClient.get<JobStatus>(`/documents/jobs/${jobId}`)
    return response.data
  },

  // Download result
  async downloadResult(jobId: string, format: 'json' | 'markdown' = 'json'): Promise<any> {
    const response = await apiClient.get(`/documents/download/${jobId}`, {
      params: { format },
    })
    return response.data
  },

  // List files
  async listFiles(page = 1, perPage = 20): Promise<any> {
    const response = await apiClient.get('/documents/files', {
      params: { page, per_page: perPage },
    })
    return response.data
  },

  // Delete file
  async deleteFile(fileId: string): Promise<void> {
    await apiClient.delete(`/documents/files/${fileId}`)
  },
}

export default apiService 