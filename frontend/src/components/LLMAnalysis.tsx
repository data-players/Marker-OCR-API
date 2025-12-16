import React, { useState } from 'react'
import { Play, Brain, Plus, Trash2, AlertCircle, CheckCircle, Loader, ChevronDown, ChevronUp, Settings, RotateCcw } from 'lucide-react'
import { 
  SchemaFieldDefinition, 
  LLMAnalysisRequest, 
  LLMAnalysisResponse,
  LLMAnalysisStatus,
  apiService 
} from '@/services/api'

interface LLMAnalysisProps {
  jobId: string
  onAnalysisComplete?: (data: Record<string, any>) => void
  onRestart?: () => void
}

interface SchemaField {
  name: string
  definition: SchemaFieldDefinition
}

const LLMAnalysis: React.FC<LLMAnalysisProps> = ({ jobId, onAnalysisComplete, onRestart }) => {
  const [introduction, setIntroduction] = useState('')
  const [schemaFields, setSchemaFields] = useState<SchemaField[]>([
    {
      name: 'filename',
      definition: {
        type: 'string',
        description: 'the name of the file',
        required: false
      }
    }
  ])
  const [isProcessing, setIsProcessing] = useState(false)
  const [analysisId, setAnalysisId] = useState<string | null>(null)
  const [analysisStatus, setAnalysisStatus] = useState<LLMAnalysisStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [parametersExpanded, setParametersExpanded] = useState(true)

  const handleAddField = () => {
    setSchemaFields([
      ...schemaFields,
      {
        name: `field_${schemaFields.length + 1}`,
        definition: {
          type: 'string',
          description: '',
          required: false
        }
      }
    ])
  }

  const handleRemoveField = (index: number) => {
    setSchemaFields(schemaFields.filter((_, i) => i !== index))
  }

  const handleFieldChange = (
    index: number,
    field: 'name' | 'type' | 'description' | 'required',
    value: any
  ) => {
    const updatedFields = [...schemaFields]
    if (field === 'name') {
      updatedFields[index].name = value
    } else if (field === 'type') {
      updatedFields[index].definition.type = value
    } else if (field === 'description') {
      updatedFields[index].definition.description = value
    } else if (field === 'required') {
      updatedFields[index].definition.required = value
    }
    setSchemaFields(updatedFields)
  }

  const validateSchema = (): boolean => {
    // Introduction is now optional, no validation needed

    if (schemaFields.length === 0) {
      setError('Please add at least one field to the schema')
      return false
    }

    for (const field of schemaFields) {
      if (!field.name.trim()) {
        setError('All fields must have a name')
        return false
      }
      if (!field.definition.description.trim()) {
        setError(`Field "${field.name}" must have a description`)
        return false
      }
    }

    return true
  }

  const handleStartAnalysis = async () => {
    setError(null)

    if (!validateSchema()) {
      return
    }

    setIsProcessing(true)
    setParametersExpanded(false)

    try {
      // Convert schema fields to schema object
      const schema: Record<string, SchemaFieldDefinition> = {}
      schemaFields.forEach(field => {
        schema[field.name] = field.definition
      })

      const request: LLMAnalysisRequest = {
        job_id: jobId,
        introduction: introduction,
        schema: schema
      }

      const response: LLMAnalysisResponse = await apiService.analyzeLLM(request)
      setAnalysisId(response.analysis_id)

      // Poll for status
      pollAnalysisStatus(response.analysis_id)
    } catch (err: any) {
      console.error('Failed to start LLM analysis:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to start analysis')
      setIsProcessing(false)
      setParametersExpanded(true)
    }
  }

  const pollAnalysisStatus = async (id: string) => {
    const maxAttempts = 60 // 60 seconds max
    let attempts = 0

    const poll = async () => {
      try {
        const status: LLMAnalysisStatus = await apiService.getLLMAnalysisStatus(id)
        setAnalysisStatus(status)

        if (status.status === 'completed') {
          setIsProcessing(false)
          if (status.extracted_data && onAnalysisComplete) {
            onAnalysisComplete(status.extracted_data)
          }
        } else if (status.status === 'failed') {
          setIsProcessing(false)
          setError(status.error_message || 'Analysis failed')
          setParametersExpanded(true)
        } else if (status.status === 'processing' && attempts < maxAttempts) {
          attempts++
          setTimeout(poll, 1000) // Poll every second
        } else if (attempts >= maxAttempts) {
          setIsProcessing(false)
          setError('Analysis timeout - please try again')
          setParametersExpanded(true)
        }
      } catch (err: any) {
        console.error('Failed to get analysis status:', err)
        setIsProcessing(false)
        setError('Failed to get analysis status')
        setParametersExpanded(true)
      }
    }

    poll()
  }

  const renderAnalysisResult = () => {
    if (!analysisStatus) return null

    if (analysisStatus.status === 'completed' && analysisStatus.extracted_data) {
      return (
        <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
            <h4 className="text-lg font-semibold text-green-900">
              Analysis Complete
            </h4>
          </div>
          <pre className="bg-white p-4 rounded border border-green-200 overflow-auto text-sm">
            {JSON.stringify(analysisStatus.extracted_data, null, 2)}
          </pre>
        </div>
      )
    }

    if (analysisStatus.status === 'failed') {
      return (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <h4 className="text-lg font-semibold text-red-900">
              Analysis Failed
            </h4>
          </div>
          <p className="text-red-700 mt-2">
            {analysisStatus.error_message}
          </p>
        </div>
      )
    }

    return null
  }

  const toggleParameters = () => {
    setParametersExpanded(!parametersExpanded)
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Brain className="h-6 w-6 text-blue-600 mr-2" />
            <div>
              <h3 className="text-xl font-bold text-gray-900">
                LLM Analysis
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Extract structured data from the OCR results using AI
              </p>
            </div>
          </div>
          {onRestart && (
            <button
              onClick={onRestart}
              className="flex items-center text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              Restart
            </button>
          )}
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
              Analysis Parameters
            </span>
          </div>
          {parametersExpanded ? (
            <ChevronUp className="h-5 w-5 text-gray-600" />
          ) : (
            <ChevronDown className="h-5 w-5 text-gray-600" />
          )}
        </button>

        {parametersExpanded && (
          <div className="px-6 pb-6">
            {/* Schema Fields */}
            <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-gray-700">
            Data Schema
          </label>
          <button
            onClick={handleAddField}
            disabled={isProcessing}
            className="flex items-center text-sm text-blue-600 hover:text-blue-700 disabled:opacity-50"
          >
            <Plus className="h-4 w-4 mr-1" />
            Add Field
          </button>
        </div>

        <div className="space-y-4">
          {schemaFields.map((field, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Field Name
                  </label>
                  <input
                    type="text"
                    value={field.name}
                    onChange={(e) => handleFieldChange(index, 'name', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                    disabled={isProcessing}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Type
                  </label>
                  <select
                    value={field.definition.type}
                    onChange={(e) => handleFieldChange(index, 'type', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                    disabled={isProcessing}
                  >
                    <option value="string">String</option>
                    <option value="number">Number</option>
                    <option value="integer">Integer</option>
                    <option value="boolean">Boolean</option>
                    <option value="array">Array</option>
                    <option value="object">Object</option>
                  </select>
                </div>
              </div>

              <div className="mb-3">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  value={field.definition.description}
                  onChange={(e) => handleFieldChange(index, 'description', e.target.value)}
                  placeholder="Describe what information to extract for this field"
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                  disabled={isProcessing}
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={field.definition.required || false}
                    onChange={(e) => handleFieldChange(index, 'required', e.target.checked)}
                    className="mr-2 rounded text-blue-600 focus:ring-blue-500"
                    disabled={isProcessing}
                  />
                  <span className="text-gray-700">Required field</span>
                </label>

                {schemaFields.length > 1 && (
                  <button
                    onClick={() => handleRemoveField(index)}
                    disabled={isProcessing}
                    className="text-red-600 hover:text-red-700 disabled:opacity-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

            {/* Task Introduction */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Task Introduction <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <textarea
                value={introduction}
                onChange={(e) => setIntroduction(e.target.value)}
                placeholder="Optionally describe what information should be extracted from the document..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={4}
                disabled={isProcessing}
              />
              <p className="text-sm text-gray-500 mt-1">
                Optional: Explain to the AI what kind of information you want to extract
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="h-5 w-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
                <div className="text-red-700 text-sm">{error}</div>
              </div>
            )}

            {/* Action Button */}
            <div className="flex justify-end">
              <button
                onClick={handleStartAnalysis}
                disabled={isProcessing}
                className="flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isProcessing ? (
                  <>
                    <Loader className="h-5 w-5 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    {analysisId ? 'Restart' : 'Start'}
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Analysis Result (shown after processing starts) */}
      {analysisId && (
        <div className="p-4 bg-gray-50">
          {renderAnalysisResult()}
        </div>
      )}
    </div>
  )
}

export default LLMAnalysis

