import React, { useState, useEffect, useRef } from 'react'
import { 
  Clock, 
  CheckCircle, 
  XCircle, 
  Loader, 
  Download, 
  Eye,
  FileText,
  Database,
  Code2
} from 'lucide-react'
import { apiService, JobStatus as JobStatusType } from '@/services/api'
import MarkdownPreview from './MarkdownPreview'
import StepProgress from './StepProgress'

interface JobStatusProps {
  jobId: string
  onComplete?: (jobStatus: JobStatusType) => void
}

const JobStatus: React.FC<JobStatusProps> = ({ jobId, onComplete }) => {
  const [jobStatus, setJobStatus] = useState<JobStatusType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)
  const [processingStartTime, setProcessingStartTime] = useState<Date | null>(null)
  const [previewFormat, setPreviewFormat] = useState<'markdown' | 'json'>('markdown')
  const [copiedMarkdown, setCopiedMarkdown] = useState(false)
  const [copiedJson, setCopiedJson] = useState(false)
  const eventSourceRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    // Fetch initial status immediately to show steps right away
    apiService.getJobStatus(jobId)
      .then((initialStatus) => {
        console.log('[JobStatus] Initial status fetched:', {
          status: initialStatus.status,
          stepsCount: initialStatus.steps?.length || 0,
          steps: initialStatus.steps
        })
        setJobStatus(initialStatus)
        setLoading(false)
        
        // Track when processing starts for the first time
        if (initialStatus.status === 'processing' && !processingStartTime) {
          setProcessingStartTime(new Date())
        }
      })
      .catch((err) => {
        console.error('[JobStatus] Failed to fetch initial status:', err)
        // Continue anyway, SSE will provide updates
      })
    
    // Use Server-Sent Events (SSE) for real-time updates instead of polling
    const cleanup = apiService.subscribeToJobStatus(
      jobId,
      (status) => {
        console.log('[JobStatus] Received status update via SSE:', {
          status: status.status,
          stepsCount: status.steps?.length || 0,
          steps: status.steps,
          stepsWithDuration: status.steps?.map(s => ({
            name: s.name,
            status: s.status,
            duration: s.duration,
            start_time: s.start_time,
            end_time: s.end_time
          })) || []
        })
        setJobStatus(status)
        setLoading(false)
        
        // Track when processing starts for the first time
        if (status.status === 'processing' && !processingStartTime) {
          setProcessingStartTime(new Date())
        }
        
        if (status.status === 'completed') {
          onComplete?.(status)
          
          // Load the result with both formats
          apiService.downloadResult(jobId, 'json')
            .then((resultData) => {
              setResult(resultData)
              // Auto-select preview format based on available formats
              const hasMarkdown = resultData.result?.markdown_content && resultData.result.markdown_content !== null && resultData.result.markdown_content !== ''
              const hasJson = resultData.result?.rich_structure && resultData.result.rich_structure !== null
              if (hasJson && !hasMarkdown) {
                // If only JSON is available, default to JSON preview
                setPreviewFormat('json')
              } else if (hasMarkdown && !hasJson) {
                // If only Markdown is available, default to Markdown preview
                setPreviewFormat('markdown')
              }
              // If both are available, keep the current selection (defaults to markdown)
            })
            .catch((err) => {
              console.error('Failed to load result:', err)
            })
        } else if (status.status === 'failed' || status.status === 'cancelled') {
          // Error message is already in status.error_message
        }
      },
      (err) => {
        console.error('SSE connection error:', err)
        // SSE is the only method for updates - no polling fallback
        setError(err.message || 'Connection error')
        setLoading(false)
      }
    )
    
    eventSourceRef.current = cleanup

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current()
        eventSourceRef.current = null
      }
    }
  }, [jobId, onComplete, processingStartTime])

  const getStatusIcon = () => {
    if (!jobStatus) return <Loader className="h-5 w-5 animate-spin text-blue-500" />
    
    switch (jobStatus.status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-500" />
      case 'processing':
        return <Loader className="h-5 w-5 animate-spin text-blue-500" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-gray-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = () => {
    if (!jobStatus) return 'bg-blue-50 border-blue-200'
    
    switch (jobStatus.status) {
      case 'pending':
        return 'bg-yellow-50 border-yellow-200'
      case 'processing':
        return 'bg-blue-50 border-blue-200'
      case 'completed':
        return 'bg-green-50 border-green-200'
      case 'failed':
        return 'bg-red-50 border-red-200'
      case 'cancelled':
        return 'bg-gray-50 border-gray-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const formatDuration = (duration: number) => {
    if (duration < 1) {
      return `${Math.round(duration * 1000)}ms`
    } else if (duration < 60) {
      return `${duration.toFixed(2)}s`
    } else {
      const minutes = Math.floor(duration / 60)
      const seconds = Math.round(duration % 60)
      return `${minutes}m ${seconds}s`
    }
  }

  const getTotalProcessingTime = () => {
    if (!jobStatus?.steps || jobStatus.steps.length === 0) {
      return null
    }
    const totalDuration = jobStatus.steps.reduce((sum, step) => sum + (step.duration || 0), 0)
    return totalDuration > 0 ? totalDuration : null
  }

  const getStatusText = () => {
    if (!jobStatus) return 'Loading...'
    
    const getProcessingDuration = () => {
      if (!processingStartTime) return 0
      return (new Date().getTime() - processingStartTime.getTime()) / 1000
    }
    
    switch (jobStatus.status) {
      case 'pending':
        return 'Queued for processing'
      case 'processing': {
        const duration = getProcessingDuration()
        if (duration > 30) {
          return 'Processing document... (downloading AI models for first use, this may take a few minutes)'
        }
        return 'Processing document...'
      }
      case 'completed':
        return 'Processing completed - Both formats generated successfully!'
      case 'failed':
        return 'Processing failed'
      case 'cancelled':
        return 'Processing cancelled'
      default:
        return jobStatus.status
    }
  }

  const handleDownload = async (format: 'json' | 'markdown') => {
    try {
      const response = await apiService.downloadResult(jobId, format)
      
      let content: string
      let filename: string
      let mimeType: string
      
      if (format === 'json') {
        // For JSON, we want the full rich structure
        content = JSON.stringify(response.result || response, null, 2)
        filename = `result-${jobId}.json`
        mimeType = 'application/json'
      } else {
        // For markdown, extract the content
        content = response.content || response.result?.markdown_content || response.result?.content || ''
        filename = `result-${jobId}.md`
        mimeType = 'text/markdown'
      }
      
      // Create download
      const blob = new Blob([content], { type: mimeType })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err: any) {
      console.error('Download failed:', err)
    }
  }

  const handleCopyJson = async () => {
    try {
      const jsonContent = JSON.stringify(result.result?.rich_structure || result.result || result, null, 2)
      await navigator.clipboard.writeText(jsonContent)
      setCopiedJson(true)
      setTimeout(() => setCopiedJson(false), 2000)
    } catch (err) {
      console.error('Failed to copy JSON: ', err)
    }
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <XCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-800">Error: {error}</span>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className={`border rounded-lg p-6 ${getStatusColor()}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center flex-1 min-w-0">
            {getStatusIcon()}
            <div className="ml-3 flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-gray-900">Processing Status</h3>
              </div>
              <p className="text-sm text-gray-600">{getStatusText()}</p>
            </div>
          </div>
        </div>

      {/* Show step progress if available, otherwise show old progress bar */}
      {/* Always show steps if they exist, even if empty (they will be populated via SSE) */}
      {jobStatus?.steps !== undefined ? (
        <div className="mb-4">
          {jobStatus.steps.length > 0 ? (
            <StepProgress 
              steps={jobStatus.steps} 
              isCompleted={jobStatus.status === 'completed'}
            />
          ) : (
            <div className="text-sm text-gray-500 italic">
              Initializing processing steps...
            </div>
          )}
        </div>
      ) : jobStatus?.progress !== undefined ? (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{jobStatus.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${jobStatus.progress}%` }}
            />
          </div>
        </div>
      ) : loading ? (
        <div className="mb-4 text-sm text-gray-500 italic">
          Connecting to processing stream...
        </div>
      ) : null}

      {jobStatus?.error_message && (
        <div className="mt-4 p-3 bg-red-100 border border-red-200 rounded">
          <p className="text-sm text-red-800">{jobStatus.error_message}</p>
        </div>
      )}

      {result && (() => {
        // Determine which formats are available
        const hasMarkdown = result.result?.markdown_content && 
                           result.result.markdown_content !== null && 
                           result.result.markdown_content !== '' &&
                           typeof result.result.markdown_content === 'string'
        const hasJson = result.result?.rich_structure && 
                       result.result.rich_structure !== null &&
                       Object.keys(result.result.rich_structure).length > 0
        
        return (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900 flex items-center">
              <Eye className="h-4 w-4 mr-2" />
              Preview
            </h4>
            
            {/* Toggle pour choisir le format de preview - only show available formats */}
            {(hasMarkdown || hasJson) && (
              <div className="flex items-center space-x-2">
                {hasMarkdown && (
                  <button
                    onClick={() => setPreviewFormat('markdown')}
                    className={`flex items-center px-3 py-1 text-sm rounded transition-colors ${
                      previewFormat === 'markdown'
                        ? 'bg-green-100 text-green-800 border border-green-300'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <FileText className="h-3 w-3 mr-1" />
                    Markdown
                  </button>
                )}
                {hasJson && (
                  <button
                    onClick={() => setPreviewFormat('json')}
                    className={`flex items-center px-3 py-1 text-sm rounded transition-colors ${
                      previewFormat === 'json'
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <Code2 className="h-3 w-3 mr-1" />
                    JSON
                  </button>
                )}
              </div>
            )}
          </div>
          
          <div className="bg-white border rounded-lg p-4 max-h-96 overflow-auto">
            {previewFormat === 'markdown' ? (
              <MarkdownPreview 
                content={result.result?.markdown_content || result.result?.content || result.content || ''} 
              />
            ) : (
              <div className="relative">
                {/* Header avec bouton copier pour JSON */}
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-200">
                  <h4 className="font-medium text-gray-900">Preview JSON</h4>
                  <button
                    onClick={handleCopyJson}
                    className="flex items-center px-2 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
                    title="Copier le JSON"
                  >
                    {copiedJson ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-1 text-green-600" />
                        Copié !
                      </>
                    ) : (
                      <>
                        <Database className="h-4 w-4 mr-1" />
                        Copier
                      </>
                    )}
                  </button>
                </div>
                <pre className="text-sm text-gray-800 whitespace-pre-wrap">
                  {JSON.stringify(result.result?.rich_structure || result.result || result, null, 2)}
                </pre>
              </div>
            )}
          </div>
          
          {/* Boutons de téléchargement déplacés sous la preview - only show available formats */}
          {jobStatus?.status === 'completed' && (hasMarkdown || hasJson) && (
            <div className="flex justify-center space-x-3 mt-4">
              {hasMarkdown && (
                <button
                  onClick={() => handleDownload('markdown')}
                  className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm transition-colors shadow-sm"
                  title="Télécharger au format Markdown"
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Télécharger Markdown
                </button>
              )}
              {hasJson && (
                <button
                  onClick={() => handleDownload('json')}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm transition-colors shadow-sm"
                  title="Télécharger la structure JSON riche"
                >
                  <Database className="h-4 w-4 mr-2" />
                  Télécharger JSON
                </button>
              )}
            </div>
          )}
        </div>
        )
      })()}

      <div className="mt-4 text-xs text-gray-500 space-y-1">
        <p>Job ID: <code className="bg-gray-100 px-1 rounded">{jobId}</code></p>
        {jobStatus?.created_at && (
          <p>Created: {new Date(jobStatus.created_at).toLocaleString()}</p>
        )}
        {jobStatus?.updated_at && (
          <p>Updated: {new Date(jobStatus.updated_at).toLocaleString()}</p>
        )}
        {result?.result?.processing_time && (
          <p>Processing time: {result.result.processing_time.toFixed(2)}s</p>
        )}
      </div>
    </div>
    </>
  )
}

export default JobStatus 