import React, { useState } from 'react'
import { Play, ArrowRight, ArrowLeft, ChevronDown, ChevronUp, Settings, Upload as UploadIcon, RotateCcw } from 'lucide-react'
import FileUpload from '@/components/FileUpload'
import ProcessingOptions from '@/components/ProcessingOptions'
import JobStatus from '@/components/JobStatus'
import LLMAnalysis from '@/components/LLMAnalysis'
import { 
  FileUploadResponse, 
  ProcessingOptions as ProcessingOptionsType,
  ProcessResponse,
  JobStatus as JobStatusType,
  apiService 
} from '@/services/api'

interface ProcessingState {
  step: 'upload' | 'processing' | 'llm-analysis'
  uploadedFile?: FileUploadResponse
  processingOptions: Partial<ProcessingOptionsType>
  currentJob?: string
  isProcessing: boolean
  jobCompleted: boolean
  parametersExpanded: boolean
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
    jobCompleted: false,
    parametersExpanded: true,
  })

  const handleFileUploaded = (uploadResponse: FileUploadResponse) => {
    setState(prev => ({
      ...prev,
      uploadedFile: uploadResponse,
      step: 'processing',
      parametersExpanded: true,
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

    setState(prev => ({ 
      ...prev, 
      isProcessing: true,
      parametersExpanded: false,
      jobCompleted: false,
    }))

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
      setState(prev => ({ 
        ...prev, 
        isProcessing: false,
        parametersExpanded: true,
      }))
      // TODO: Show error toast
    }
  }

  const handleJobComplete = (jobStatus: JobStatusType) => {
    // Job completed, show choice between new document or LLM analysis
    console.log('Job completed successfully!')
    setState(prev => ({ ...prev, jobCompleted: true }))
  }

  const handleStartLLMAnalysis = () => {
    setState(prev => ({ ...prev, step: 'llm-analysis' }))
  }

  const handleLLMAnalysisComplete = (data: Record<string, any>) => {
    console.log('LLM analysis completed:', data)
    // Could show success toast or store the data
  }

  const resetWorkflow = () => {
    setState({
      step: 'upload',
      processingOptions: {
        output_format: 'markdown',
        force_ocr: false,
        extract_images: false,
        paginate_output: false,
        language: 'auto',
      },
      isProcessing: false,
      jobCompleted: false,
      parametersExpanded: true,
    })
  }

  const toggleParameters = () => {
    setState(prev => ({ 
      ...prev, 
      parametersExpanded: !prev.parametersExpanded 
    }))
  }

  const renderStepIndicator = () => {
    const steps = [
      { key: 'upload', label: 'Upload', completed: !!state.uploadedFile },
      { key: 'processing', label: 'OCR', completed: state.jobCompleted },
      { key: 'llm-analysis', label: 'LLM', completed: false },
    ]

    return (
      <div className="flex items-center justify-center">
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
        {renderStepIndicator()}
      </div>

      <div className="space-y-6">
        {/* Step 1: Upload */}
        {state.step === 'upload' && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center">
                <UploadIcon className="h-6 w-6 text-green-600 mr-2" />
                <div>
                  <h3 className="text-xl font-bold text-gray-900">
                    Upload Document
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    Select a PDF document to process with OCR
                  </p>
                </div>
              </div>
            </div>

            {/* Upload Area */}
            <div className="p-6">
              <FileUpload 
                onFileUploaded={handleFileUploaded}
                disabled={state.isProcessing}
              />
            </div>
          </div>
        )}

        {/* Step 2: OCR Processing (with options accordion) */}
        {state.step === 'processing' && (
          <>
            <div className="bg-white rounded-lg shadow overflow-hidden">
              {/* Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center flex-1">
                    <Play className="h-6 w-6 text-blue-600 mr-2" />
                    <div>
                      <h3 className="text-xl font-bold text-gray-900">
                        OCR Processing
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {state.uploadedFile?.filename} ({state.uploadedFile?.size ? (state.uploadedFile.size / 1024 / 1024).toFixed(2) : '?'} MB)
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={resetWorkflow}
                    className="flex items-center text-sm text-gray-600 hover:text-gray-800 transition-colors"
                  >
                    <RotateCcw className="h-4 w-4 mr-1" />
                    Restart
                  </button>
                </div>
              </div>

              {/* Parameters Accordion */}
              <div className="border-b border-gray-200">
                <button
                  onClick={toggleParameters}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center">
                    <Settings className="h-5 w-5 text-gray-600 mr-2" />
                    <span className="font-medium text-gray-900">
                      OCR Options
                    </span>
                  </div>
                  {state.parametersExpanded ? (
                    <ChevronUp className="h-5 w-5 text-gray-600" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-gray-600" />
                  )}
                </button>
                
                {state.parametersExpanded && (
                  <div className="px-6 pb-6">
                    <ProcessingOptions
                      onOptionsChange={handleOptionsChange}
                      initialOptions={state.processingOptions}
                      disabled={state.isProcessing}
                      compact={true}
                    />
                    
                    {/* Start/Restart OCR Button */}
                    <div className="mt-6 flex justify-end">
                      <button
                        onClick={handleStartProcessing}
                        disabled={state.isProcessing}
                        className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        <Play className="h-5 w-5 mr-2" />
                        {state.currentJob 
                          ? (state.isProcessing ? 'Processing...' : 'Restart')
                          : (state.isProcessing ? 'Processing...' : 'Start')
                        }
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Action buttons after OCR completion */}
              {state.currentJob && state.jobCompleted && (
                <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
                  <div className="flex items-center justify-center space-x-3">
                    <button
                      onClick={resetWorkflow}
                      className="flex items-center px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors bg-white"
                    >
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      New Document
                    </button>
                    <button
                      onClick={handleStartLLMAnalysis}
                      className="flex items-center px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      LLM Analysis
                      <ArrowRight className="h-4 w-4 ml-2" />
                    </button>
                  </div>
                </div>
              )}

              {/* Job Status (if processing has started) */}
              {state.currentJob && (
                <div className="p-4 bg-gray-50">
                  <JobStatus
                    jobId={state.currentJob}
                    onComplete={handleJobComplete}
                  />
                </div>
              )}
            </div>
          </>
        )}

        {/* Step 3: LLM Analysis */}
        {state.step === 'llm-analysis' && state.currentJob && (
          <LLMAnalysis
            jobId={state.currentJob}
            onAnalysisComplete={handleLLMAnalysisComplete}
            onRestart={resetWorkflow}
          />
        )}
      </div>
    </div>
  )
}

export default ProcessDocument 