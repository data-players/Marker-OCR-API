import React, { useState } from 'react'
import { Play, ArrowRight } from 'lucide-react'
import FileUpload from '@/components/FileUpload'
import ProcessingOptions from '@/components/ProcessingOptions'
import JobStatus from '@/components/JobStatus'
import { 
  FileUploadResponse, 
  ProcessingOptions as ProcessingOptionsType,
  ProcessResponse,
  apiService 
} from '@/services/api'

interface ProcessingState {
  step: 'upload' | 'configure' | 'processing'
  uploadedFile?: FileUploadResponse
  processingOptions: Partial<ProcessingOptionsType>
  currentJob?: string
  isProcessing: boolean
}

const ProcessDocument: React.FC = () => {
  const [state, setState] = useState<ProcessingState>({
    step: 'upload',
    processingOptions: {
      output_format: 'markdown',
      force_ocr: false,
      extract_images: false,
      paginate_output: false,
      language: 'auto',
    },
    isProcessing: false,
  })

  const handleFileUploaded = (uploadResponse: FileUploadResponse) => {
    setState(prev => ({
      ...prev,
      uploadedFile: uploadResponse,
      step: 'configure',
    }))
  }

  const handleOptionsChange = (options: Partial<ProcessingOptionsType>) => {
    setState(prev => ({
      ...prev,
      processingOptions: { ...prev.processingOptions, ...options },
    }))
  }

  const handleStartProcessing = async () => {
    if (!state.uploadedFile) return

    setState(prev => ({ ...prev, isProcessing: true }))

    try {
      const response: ProcessResponse = await apiService.processDocument(
        state.uploadedFile.file_id,
        state.processingOptions
      )

      setState(prev => ({
        ...prev,
        currentJob: response.job_id,
        step: 'processing',
        isProcessing: false,
      }))
    } catch (error: any) {
      console.error('Failed to start processing:', error)
      setState(prev => ({ ...prev, isProcessing: false }))
      // TODO: Show error toast
    }
  }

  const handleJobComplete = () => {
    // Job completed, could show success message or reset
    console.log('Job completed successfully!')
  }

  const resetWorkflow = () => {
    setState({
      step: 'upload',
      processingOptions: {
        output_format: 'both',
        force_ocr: false,
        extract_images: true,
        paginate_output: false,
        language: 'auto',
      },
      isProcessing: false,
    })
  }

  const renderStepIndicator = () => {
    const steps = [
      { key: 'upload', label: 'Upload', completed: !!state.uploadedFile },
      { key: 'configure', label: 'Configure', completed: state.step === 'processing' },
      { key: 'processing', label: 'Process', completed: false },
    ]

    return (
      <div className="flex items-center justify-center mb-8">
        {steps.map((step, index) => (
          <React.Fragment key={step.key}>
            <div className="flex items-center">
              <div
                className={`
                  w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                  ${
                    step.completed || state.step === step.key
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }
                `}
              >
                {index + 1}
              </div>
              <span
                className={`
                  ml-2 text-sm font-medium
                  ${
                    step.completed || state.step === step.key
                      ? 'text-blue-600'
                      : 'text-gray-500'
                  }
                `}
              >
                {step.label}
              </span>
            </div>
            {index < steps.length - 1 && (
              <ArrowRight className="h-4 w-4 text-gray-400 mx-4" />
            )}
          </React.Fragment>
        ))}
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Process Document
        </h2>
        <p className="text-gray-600">
          Upload and process PDF documents using the Marker OCR API.
        </p>
      </div>

      {renderStepIndicator()}

      <div className="space-y-6">
        {/* Step 1: Upload */}
        {state.step === 'upload' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Upload Your PDF Document
            </h3>
            <FileUpload 
              onFileUploaded={handleFileUploaded}
              disabled={state.isProcessing}
            />
          </div>
        )}

        {/* Step 2: Configure */}
        {state.step === 'configure' && (
          <>
            {/* File Summary */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Uploaded File
              </h3>
              <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                <div>
                  <p className="font-medium text-green-900">
                    {state.uploadedFile?.filename}
                  </p>
                  <p className="text-sm text-green-700">
                    Size: {state.uploadedFile?.size ? (state.uploadedFile.size / 1024 / 1024).toFixed(2) : '?'} MB
                  </p>
                </div>
                <button
                  onClick={resetWorkflow}
                  className="text-green-700 hover:text-green-800 underline text-sm"
                >
                  Upload different file
                </button>
              </div>
            </div>

            {/* Processing Options */}
            <ProcessingOptions
              onOptionsChange={handleOptionsChange}
              disabled={state.isProcessing}
            />

            {/* Start Processing Button */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Ready to Process
                  </h3>
                  <p className="text-gray-600">
                    Start processing your document with the selected options.
                  </p>
                </div>
                <button
                  onClick={handleStartProcessing}
                  disabled={state.isProcessing}
                  className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Play className="h-5 w-5 mr-2" />
                  {state.isProcessing ? 'Starting...' : 'Start Processing'}
                </button>
              </div>
            </div>
          </>
        )}

        {/* Step 3: Processing */}
        {state.step === 'processing' && state.currentJob && (
          <>
            <JobStatus
              jobId={state.currentJob}
              onComplete={handleJobComplete}
            />
            
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Process Another Document
                  </h3>
                  <p className="text-gray-600">
                    Start a new processing job with a different document.
                  </p>
                </div>
                <button
                  onClick={resetWorkflow}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  New Document
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default ProcessDocument 