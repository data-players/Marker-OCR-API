import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import { apiService, FileUploadResponse } from '@/services/api'

interface FileUploadProps {
  onFileUploaded: (uploadResponse: FileUploadResponse) => void
  disabled?: boolean
}

interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  file?: File
  uploadResponse?: FileUploadResponse
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded, disabled = false }) => {
  const [uploadState, setUploadState] = useState<UploadState>({
    status: 'idle',
    progress: 0,
  })

  const handleUpload = async (file: File) => {
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

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0 && !disabled) {
        handleUpload(acceptedFiles[0])
      }
    },
    [disabled]
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
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="w-full">
      {uploadState.status === 'idle' && (
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

      {uploadState.status === 'uploading' && (
        <div className="border rounded-lg p-6">
          <div className="flex items-center mb-4">
            <File className="h-8 w-8 text-blue-500 mr-3" />
            <div className="flex-1">
              <p className="font-medium text-gray-900">{uploadState.file?.name}</p>
              <p className="text-sm text-gray-500">
                {uploadState.file && formatFileSize(uploadState.file.size)}
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
                <p className="font-medium text-green-900">{uploadState.file?.name}</p>
                <p className="text-sm text-green-700">Upload successful</p>
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
            <p>Size: {uploadState.file && formatFileSize(uploadState.file.size)}</p>
          </div>
        </div>
      )}

      {uploadState.status === 'error' && (
        <div className="border border-red-200 bg-red-50 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <AlertCircle className="h-8 w-8 text-red-500 mr-3" />
              <div>
                <p className="font-medium text-red-900">{uploadState.file?.name}</p>
                <p className="text-sm text-red-700">Upload failed</p>
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