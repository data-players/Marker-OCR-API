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
  output_format: 'json' | 'markdown'
  force_ocr: boolean
  extract_images: boolean
  paginate_output: boolean
  language?: string
}

export interface ProcessResponse {
  job_id: string
  status: string
  estimated_time?: number
}

export interface SubStep {
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  start_time?: number
  end_time?: number
  duration?: number
}

export interface ProcessingStep {
  name: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  start_time?: number
  end_time?: number
  duration?: number
  sub_steps?: string[]
  sub_steps_detailed?: SubStep[]
  current_sub_step?: string
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  created_at: string
  updated_at: string
  progress?: number
  steps?: ProcessingStep[]
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

  // Upload file from URL
  async uploadFileFromUrl(url: string): Promise<FileUploadResponse> {
    const formData = new FormData()
    formData.append('url', url)
    
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
    // Use the provided output_format, default to 'markdown' if not specified
    formData.append('output_format', options.output_format || 'markdown')
    formData.append('force_ocr', String(options.force_ocr || false))
    formData.append('extract_images', String(options.extract_images !== false))
    formData.append('paginate_output', String(options.paginate_output === true))
    
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

  // Server-Sent Events for real-time job status updates
  subscribeToJobStatus(
    jobId: string,
    onUpdate: (status: JobStatus) => void,
    onError?: (error: Error) => void
  ): () => void {
    const baseURL = API_BASE_URL || 'http://localhost:8000'
    const url = `${baseURL}/api/v1/documents/jobs/${jobId}/stream`
    
    console.log(`[SSE] Connecting to ${url} for job ${jobId}`)
    const eventSource = new EventSource(url)
    
    // Track if we've received a final status (completed/failed/cancelled)
    // This prevents reporting errors when connection closes normally after completion
    let hasReceivedFinalStatus = false
    let errorReportTimeout: NodeJS.Timeout | null = null
    
    eventSource.onopen = () => {
      console.log(`[SSE] Connection opened for job ${jobId}`)
    }
    
    eventSource.onmessage = (event) => {
      console.log(`[SSE] Message received for job ${jobId}:`, event.data)
      try {
        const data = JSON.parse(event.data)
        
        // Handle error messages
        if (data.error) {
          const error = new Error(data.error)
          onError?.(error)
          eventSource.close()
          return
        }
        
        // Convert to JobStatus format
        const jobStatus: JobStatus = {
          job_id: data.job_id || jobId,
          status: data.status,
          created_at: data.created_at?.toString() || new Date().toISOString(),
          updated_at: data.updated_at?.toString() || new Date().toISOString(),
          progress: data.progress,
          steps: data.steps || [], // Ensure steps is always an array, even if empty
          result: data.result,
          error_message: data.error_message
        }
        
        console.log(`[SSE] Parsed job status:`, {
          status: jobStatus.status,
          stepsCount: jobStatus.steps?.length || 0,
          steps: jobStatus.steps
        })
        
        onUpdate(jobStatus)
        
        // Track if we've received a final status
        if (['completed', 'failed', 'cancelled'].includes(data.status)) {
          hasReceivedFinalStatus = true
          // Clear any pending error timeout since we're closing normally
          if (errorReportTimeout) {
            clearTimeout(errorReportTimeout)
            errorReportTimeout = null
          }
          // Close connection after a short delay to ensure final update is processed
          setTimeout(() => {
            eventSource.close()
          }, 100)
        }
      } catch (err) {
        console.error('Failed to parse SSE message:', err)
        onError?.(err as Error)
      }
    }
    
    eventSource.onerror = (error) => {
      console.error(`[SSE] Connection error for job ${jobId}:`, error)
      console.error(`[SSE] EventSource readyState:`, eventSource.readyState)
      // readyState: 0 = CONNECTING, 1 = OPEN, 2 = CLOSED
      
      // If we've already received a final status, ignore errors (connection closed normally)
      if (hasReceivedFinalStatus) {
        console.log(`[SSE] Connection closed normally after job completion for ${jobId}`)
        return
      }
      
      // Only report error if connection is actually closed
      // onerror can fire during reconnection attempts, which is normal
      if (eventSource.readyState === EventSource.CLOSED) {
        console.error(`[SSE] Connection closed unexpectedly for job ${jobId}`)
        // Don't call onError immediately - EventSource will try to reconnect automatically
        // Only report error after multiple failed attempts
        // Clear any existing timeout first
        if (errorReportTimeout) {
          clearTimeout(errorReportTimeout)
        }
        errorReportTimeout = setTimeout(() => {
          // Double-check that we still haven't received final status
          if (!hasReceivedFinalStatus && eventSource.readyState === EventSource.CLOSED) {
            onError?.(new Error('SSE connection closed'))
            eventSource.close()
          }
          errorReportTimeout = null
        }, 5000) // Wait 5 seconds before reporting error
      } else if (eventSource.readyState === EventSource.CONNECTING) {
        // Connection is reconnecting, this is normal - don't report error
        console.log(`[SSE] Reconnecting for job ${jobId}...`)
      } else {
        // Connection is open but error occurred - might be temporary
        console.warn(`[SSE] Temporary error (readyState: ${eventSource.readyState}) for job ${jobId}, will retry`)
      }
      // Don't close connection on first error - let EventSource handle reconnection
    }
    
    // Return cleanup function
    return () => {
      if (errorReportTimeout) {
        clearTimeout(errorReportTimeout)
      }
      eventSource.close()
    }
  },
}

export default apiService 