import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle, Link as LinkIcon } from 'lucide-react'
import { apiService, FileUploadResponse } from '@/services/api'

interface FileUploadProps {
  onFileUploaded: (uploadResponse: FileUploadResponse) => void
  disabled?: boolean
}

type UploadMode = 'file' | 'url'

interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  file?: File
  url?: string
  uploadResponse?: FileUploadResponse
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded, disabled = false }) => {
  const [uploadMode, setUploadMode] = useState<UploadMode>('file')
  const [urlInput, setUrlInput] = useState('')
  const [uploadState, setUploadState] = useState<UploadState>({
    status: 'idle',
    progress: 0,
  })

  const handleFileUpload = async (file: File) => {
    setUploadState({
      status: 'uploading',
      progress: 0,
      file,
    })

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90),
        }))
      }, 200)

      const uploadResponse = await apiService.uploadFile(file)
      
      clearInterval(progressInterval)
      
      setUploadState({
        status: 'success',
        progress: 100,
        file,
        uploadResponse,
      })

      onFileUploaded(uploadResponse)
    } catch (error: any) {
      setUploadState({
        status: 'error',
        progress: 0,
        file,
        error: error.response?.data?.detail || error.message || 'Upload failed',
      })
    }
  }

  const handleUrlUpload = async () => {
    if (!urlInput.trim()) {
      setUploadState({
        status: 'error',
        progress: 0,
        url: urlInput,
        error: 'Please enter a valid URL',
      })
      return
    }

    // Basic URL validation
    try {
      new URL(urlInput)
    } catch {
      setUploadState({
        status: 'error',
        progress: 0,
        url: urlInput,
        error: 'Invalid URL format',
      })
      return
    }

    setUploadState({
      status: 'uploading',
      progress: 0,
      url: urlInput,
    })

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadState(prev => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90),
        }))
      }, 200)

      const uploadResponse = await apiService.uploadFileFromUrl(urlInput)
      
      clearInterval(progressInterval)
      
      setUploadState({
        status: 'success',
        progress: 100,
        url: urlInput,
        uploadResponse,
      })

      onFileUploaded(uploadResponse)
    } catch (error: any) {
      setUploadState({
        status: 'error',
        progress: 0,
        url: urlInput,
        error: error.response?.data?.detail || error.message || 'Download failed',
      })
    }
  }

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0 && !disabled && uploadMode === 'file') {
        handleFileUpload(acceptedFiles[0])
      }
    },
    [disabled, uploadMode]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled,
  })

  const resetUpload = () => {
    setUploadState({
      status: 'idle',
      progress: 0,
    })
    setUrlInput('')
  }
  
  // Expose handleUrlUpload to window for browser testing
  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).testUploadFromUrl = async (url: string) => {
        // Switch to URL mode if not already
        setUploadMode('url')
        // Set the URL input
        setUrlInput(url)
        // Wait for state update then trigger upload
        setTimeout(async () => {
          if (!url.trim()) {
            console.error('URL vide')
            return
          }
          try {
            new URL(url)
          } catch {
            console.error('URL invalide:', url)
            return
          }
          
          setUploadState({
            status: 'uploading',
            progress: 0,
            url: url,
          })

          try {
            const progressInterval = setInterval(() => {
              setUploadState(prev => ({
                ...prev,
                progress: Math.min(prev.progress + 10, 90),
              }))
            }, 200)

            const uploadResponse = await apiService.uploadFileFromUrl(url)
            
            clearInterval(progressInterval)
            
            setUploadState({
              status: 'success',
              progress: 100,
              url: url,
              uploadResponse,
            })

            onFileUploaded(uploadResponse)
          } catch (error: any) {
            setUploadState({
              status: 'error',
              progress: 0,
              url: url,
              error: error.response?.data?.detail || error.message || 'Download failed',
            })
          }
        }, 200)
      }
    }
  }, [onFileUploaded])

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="w-full">
      {/* Mode selector */}
      {uploadState.status === 'idle' && (
        <div className="flex mb-4 bg-gray-100 rounded-lg p-1">
          <button
            type="button"
            onClick={() => {
              setUploadMode('file')
              resetUpload()
            }}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              uploadMode === 'file'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            disabled={disabled}
          >
            <Upload className="h-4 w-4 inline mr-2" />
            Upload File
          </button>
          <button
            type="button"
            onClick={() => {
              setUploadMode('url')
              resetUpload()
            }}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              uploadMode === 'url'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
            disabled={disabled}
          >
            <LinkIcon className="h-4 w-4 inline mr-2" />
            From URL
          </button>
        </div>
      )}

      {uploadState.status === 'idle' && uploadMode === 'file' && (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive 
              ? 'border-blue-400 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          <Upload className={`mx-auto h-12 w-12 mb-4 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
          
          {isDragActive ? (
            <p className="text-blue-600 text-lg font-medium">Drop your PDF here...</p>
          ) : (
            <div>
              <p className="text-gray-600 text-lg font-medium mb-2">
                Drag & drop your PDF here, or click to select
              </p>
              <p className="text-gray-500 text-sm">
                Only PDF files are supported (max 50MB)
              </p>
            </div>
          )}
        </div>
      )}

      {uploadState.status === 'idle' && uploadMode === 'url' && (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <LinkIcon className="h-4 w-4 inline mr-1" />
              PDF Document URL
            </label>
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://example.com/document.pdf"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={disabled}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !disabled) {
                  handleUrlUpload()
                }
              }}
            />
            <p className="mt-2 text-sm text-gray-500">
              Enter a direct link to a PDF file (HTTP/HTTPS)
            </p>
            {/* Test button for browser automation */}
            {process.env.NODE_ENV === 'development' && (
              <button
                onClick={async () => {
                  const testUrl = 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'
                  setUrlInput(testUrl)
                  // Wait for React state update, then trigger upload
                  await new Promise(resolve => setTimeout(resolve, 200))
                  // Call handleUrlUpload directly with the URL
                  if (!testUrl.trim()) {
                    setUploadState({
                      status: 'error',
                      progress: 0,
                      url: testUrl,
                      error: 'Please enter a valid URL',
                    })
                    return
                  }
                  try {
                    new URL(testUrl)
                  } catch {
                    setUploadState({
                      status: 'error',
                      progress: 0,
                      url: testUrl,
                      error: 'Invalid URL format',
                    })
                    return
                  }
                  setUploadState({
                    status: 'uploading',
                    progress: 0,
                    url: testUrl,
                  })
                  try {
                    const progressInterval = setInterval(() => {
                      setUploadState(prev => ({
                        ...prev,
                        progress: Math.min(prev.progress + 10, 90),
                      }))
                    }, 200)
                    const uploadResponse = await apiService.uploadFileFromUrl(testUrl)
                    clearInterval(progressInterval)
                    setUploadState({
                      status: 'success',
                      progress: 100,
                      url: testUrl,
                      uploadResponse,
                    })
                    onFileUploaded(uploadResponse)
                  } catch (error: any) {
                    setUploadState({
                      status: 'error',
                      progress: 0,
                      url: testUrl,
                      error: error.response?.data?.detail || error.message || 'Download failed',
                    })
                  }
                }}
                className="mt-2 w-full px-3 py-1.5 text-xs bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                title="Test button for browser automation"
              >
                🧪 Test avec URL exemple
              </button>
            )}
          </div>
          <button
            onClick={handleUrlUpload}
            disabled={disabled || !urlInput.trim()}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Download & Upload
          </button>
        </div>
      )}

      {uploadState.status === 'uploading' && (
        <div className="border rounded-lg p-6">
          <div className="flex items-center mb-4">
            {uploadMode === 'file' ? (
              <File className="h-8 w-8 text-blue-500 mr-3" />
            ) : (
              <LinkIcon className="h-8 w-8 text-blue-500 mr-3" />
            )}
            <div className="flex-1">
              <p className="font-medium text-gray-900">
                {uploadMode === 'file' 
                  ? uploadState.file?.name 
                  : uploadState.url}
              </p>
              <p className="text-sm text-gray-500">
                {uploadMode === 'file' && uploadState.file
                  ? formatFileSize(uploadState.file.size)
                  : 'Downloading from URL...'}
              </p>
            </div>
          </div>
          
          <div className="mb-2">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Uploading...</span>
              <span>{uploadState.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadState.progress}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {uploadState.status === 'success' && (
        <div className="border border-green-200 bg-green-50 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <CheckCircle className="h-8 w-8 text-green-500 mr-3" />
              <div>
                <p className="font-medium text-green-900">
                  {uploadMode === 'file' 
                    ? uploadState.file?.name 
                    : uploadState.url}
                </p>
                <p className="text-sm text-green-700">
                  {uploadMode === 'file' ? 'Upload' : 'Download'} successful
                </p>
              </div>
            </div>
            <button
              onClick={resetUpload}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <div className="text-sm text-green-700">
            <p>File ID: <code className="bg-green-100 px-2 py-1 rounded">{uploadState.uploadResponse?.file_id}</code></p>
            {uploadState.uploadResponse && (
              <p>Size: {formatFileSize(uploadState.uploadResponse.size)}</p>
            )}
            {uploadState.uploadResponse?.filename && (
              <p>Filename: {uploadState.uploadResponse.filename}</p>
            )}
          </div>
        </div>
      )}

      {uploadState.status === 'error' && (
        <div className="border border-red-200 bg-red-50 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <AlertCircle className="h-8 w-8 text-red-500 mr-3" />
              <div>
                <p className="font-medium text-red-900">
                  {uploadMode === 'file' 
                    ? uploadState.file?.name 
                    : uploadState.url || 'Invalid input'}
                </p>
                <p className="text-sm text-red-700">
                  {uploadMode === 'file' ? 'Upload' : 'Download'} failed
                </p>
              </div>
            </div>
            <button
              onClick={resetUpload}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          
          <div className="text-sm text-red-700 mb-4">
            <p>{uploadState.error}</p>
          </div>
          
          <button
            onClick={resetUpload}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  )
}

export default FileUpload 