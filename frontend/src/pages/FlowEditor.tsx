import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'
import { ChevronDown, ChevronUp, Settings } from 'lucide-react'
import SchemaEditor, {
  SchemaField as EditorSchemaField,
  fieldsToSchemaWithRoot,
  parseSchemaWithRoot,
  createInitialFields
} from '@/components/SchemaEditor'
import ProcessingOptions from '@/components/ProcessingOptions'
import { ProcessingOptions as ProcessingOptionsType } from '@/services/api'

interface SchemaFieldDef {
  type: string
  description: string
  required: boolean
}

interface Flow {
  id: string
  workspace_id: string
  name: string
  description: string | null
  api_key: string
  extraction_schema: Record<string, SchemaFieldDef>
  introduction: string
  ocr_options: Record<string, any>
  is_active: boolean
}

interface Execution {
  id: string
  input_type: string
  input_source: string
  status: string
  extracted_data: Record<string, any> | null
  error_message: string | null
  processing_time: number | null
  created_at: string
}

export default function FlowEditor() {
  const { workspaceId, flowId } = useParams<{ workspaceId: string; flowId: string }>()
  const { token } = useAuth()
  const navigate = useNavigate()

  const [flow, setFlow] = useState<Flow | null>(null)
  const [executions, setExecutions] = useState<Execution[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'editor' | 'api' | 'history'>('editor')

  // Form state
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [introduction, setIntroduction] = useState('')
  const [schemaFields, setSchemaFields] = useState<EditorSchemaField[]>(createInitialFields())
  const [ocrOptions, setOcrOptions] = useState<Partial<ProcessingOptionsType>>({
    output_format: 'markdown',
    force_ocr: false,
    extract_images: false,
    paginate_output: false,
    language: 'auto',
  })
  const [showOcrOptions, setShowOcrOptions] = useState(false)

  // Test state
  const [testUrl, setTestUrl] = useState('')
  const [testFile, setTestFile] = useState<File | null>(null)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [testSteps, setTestSteps] = useState<any[]>([])
  const [currentStep, setCurrentStep] = useState<string | null>(null)
  const [elapsedTime, setElapsedTime] = useState<number>(0)
  const [testStartTime, setTestStartTime] = useState<number | null>(null)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchFlow()
    fetchExecutions()
  }, [flowId])

  // Timer for elapsed time during testing
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null

    if (isTesting && testStartTime) {
      interval = setInterval(() => {
        setElapsedTime((Date.now() - testStartTime) / 1000)
      }, 100)
    } else {
      setElapsedTime(0)
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isTesting, testStartTime])

  const fetchFlow = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/workspaces/${workspaceId}/flows/${flowId}`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      if (response.ok) {
        const data = await response.json()
        setFlow(data)
        setName(data.name)
        setDescription(data.description || '')
        setIntroduction(data.introduction || '')
        // Parse schema to fields
        if (data.extraction_schema && Object.keys(data.extraction_schema).length > 0) {
          const fields = parseSchemaWithRoot(data.extraction_schema)
          setSchemaFields(fields)
        } else {
          setSchemaFields(createInitialFields())
        }
        // Load OCR options
        if (data.ocr_options) {
          setOcrOptions({
            output_format: data.ocr_options.output_format || 'markdown',
            force_ocr: data.ocr_options.force_ocr || false,
            extract_images: data.ocr_options.extract_images || false,
            paginate_output: data.ocr_options.paginate_output || false,
            language: data.ocr_options.language || 'auto',
          })
        }
      } else {
        navigate(`/workspace/${workspaceId}`)
      }
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setIsLoading(false)
    }
  }

  const fetchExecutions = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/workspaces/${workspaceId}/flows/${flowId}/executions?limit=20`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      )

      if (response.ok) {
        const data = await response.json()
        setExecutions(data.executions)
      }
    } catch (error) {
      console.error('Failed to fetch executions')
    }
  }

  const saveFlow = async () => {
    // Convert editor fields to JSON schema (root is always object)
    const extractionSchema = fieldsToSchemaWithRoot(schemaFields)

    // Validate: must have at least one field
    if (schemaFields.length === 0) {
      toast.error('Ajoutez au moins un champ au schéma')
      return
    }

    setIsSaving(true)
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/workspaces/${workspaceId}/flows/${flowId}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name,
            description: description || null,
            introduction,
            extraction_schema: extractionSchema,
            ocr_options: ocrOptions
          })
        }
      )

      if (response.ok) {
        const updated = await response.json()
        setFlow(updated)
        toast.success('Flow sauvegardé !')
      } else {
        toast.error('Erreur lors de la sauvegarde')
      }
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde')
    } finally {
      setIsSaving(false)
    }
  }

  const startAsyncExtraction = async (endpoint: string, body: FormData | string, headers?: Record<string, string>) => {
    setIsTesting(true)
    setTestResult(null)
    setTestSteps([])
    setCurrentStep(null)
    setTestStartTime(Date.now())
    setElapsedTime(0)

    try {
      // Start async extraction
      const response = await fetch(`${API_BASE_URL}/api/v1/extract/${flow?.api_key}/async`, {
        method: 'POST',
        headers: headers,
        body: body
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to start extraction')
      }

      const data = await response.json()
      const executionId = data.execution_id

      // Poll for status updates
      const pollStatus = async () => {
        try {
          const statusResponse = await fetch(
            `${API_BASE_URL}/api/v1/extract/${flow?.api_key}/status/${executionId}`
          )

          if (!statusResponse.ok) {
            throw new Error('Failed to get status')
          }

          const execData = await statusResponse.json()

          // Update steps
          if (execData.steps) {
            setTestSteps(execData.steps)
          }

          // Update current step
          if (execData.current_step) {
            setCurrentStep(execData.current_step)
          }

          // Check if completed or failed
          if (execData.status === 'completed') {
            setTestSteps(execData.steps || [])
            setTestResult({
              execution_id: execData.execution_id,
              status: 'completed',
              extracted_data: execData.extracted_data,
              processing_time: execData.processing_time
            })
            setIsTesting(false)
            setCurrentStep(null)
            setTestStartTime(null)
            fetchExecutions()
            toast.success('Extraction réussie !')
            return true // Stop polling
          } else if (execData.status === 'failed') {
            setTestSteps(execData.steps || [])
            setTestResult({
              execution_id: execData.execution_id,
              status: 'failed',
              error_message: execData.error_message,
              processing_time: execData.processing_time
            })
            setIsTesting(false)
            setCurrentStep(null)
            setTestStartTime(null)
            fetchExecutions()
            toast.error(execData.error_message || 'Échec de l\'extraction')
            return true // Stop polling
          }

          return false // Continue polling
        } catch (e) {
          console.error('Error polling status:', e)
          return false // Continue polling on error
        }
      }

      // Start polling every 2 seconds
      const pollInterval = setInterval(async () => {
        const isDone = await pollStatus()
        if (isDone) {
          clearInterval(pollInterval)
        }
      }, 2000)

      // Set a timeout to stop polling after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval)
        if (isTesting) {
          setIsTesting(false)
          setCurrentStep(null)
          setTestStartTime(null)
          toast.error('Timeout: Le traitement prend trop de temps. Vérifiez l\'historique.')
          fetchExecutions()
        }
      }, 5 * 60 * 1000)

    } catch (error: any) {
      toast.error(error.message || 'Erreur lors du test')
      setIsTesting(false)
      setCurrentStep(null)
      setTestStartTime(null)
    }
  }

  const testWithUrl = async () => {
    if (!testUrl) {
      toast.error('Entrez une URL')
      return
    }

    await startAsyncExtraction(
      `${API_BASE_URL}/api/v1/extract/${flow?.api_key}/async`,
      JSON.stringify({ url: testUrl }),
      { 'Content-Type': 'application/json' }
    )
  }

  const testWithFile = async () => {
    if (!testFile) {
      toast.error('Sélectionnez un fichier')
      return
    }

    const formData = new FormData()
    formData.append('file', testFile)

    await startAsyncExtraction(
      `${API_BASE_URL}/api/v1/extract/${flow?.api_key}/async`,
      formData
    )
  }

  const copyApiKey = () => {
    if (flow) {
      navigator.clipboard.writeText(flow.api_key)
      toast.success('Clé API copiée !')
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-purple-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Link to={`/workspace/${workspaceId}`} className="text-gray-400 hover:text-white transition">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="text-xl font-bold text-white bg-transparent border-none focus:outline-none focus:ring-2 focus:ring-purple-500 rounded px-2 -mx-2"
            />
          </div>
          <button
            onClick={saveFlow}
            disabled={isSaving}
            className="px-4 py-2 rounded-lg bg-purple-500 text-white hover:bg-purple-600 transition disabled:opacity-50"
          >
            {isSaving ? 'Sauvegarde...' : 'Sauvegarder'}
          </button>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4">
          <nav className="flex space-x-6">
            {[
              { id: 'editor', label: '✏️ Éditeur', description: 'Schéma & Test' },
              { id: 'api', label: '🔗 API' },
              { id: 'history', label: '📜 Historique' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 border-b-2 font-medium transition ${activeTab === tab.id
                  ? 'border-purple-500 text-white'
                  : 'border-transparent text-gray-400 hover:text-white'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="mx-auto px-4 py-6">
        {activeTab === 'editor' && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 items-start">
            {/* Left Column - Schema Configuration */}
            <div className="space-y-4">
              {/* Introduction */}
              <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  🎯 Instructions pour le LLM
                </label>
                <textarea
                  value={introduction}
                  onChange={(e) => setIntroduction(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                  placeholder="Décrivez ce que vous souhaitez extraire de ce type de document..."
                />
              </div>

              {/* OCR Options Accordion */}
              <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                <button
                  onClick={() => setShowOcrOptions(!showOcrOptions)}
                  className="w-full px-5 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Settings className="h-4 w-4 text-gray-400" />
                    <span className="text-sm font-medium text-gray-300">
                      Options OCR
                    </span>
                    <span className="text-xs text-gray-500">
                      ({ocrOptions.output_format}, {ocrOptions.language})
                    </span>
                  </div>
                  {showOcrOptions ? (
                    <ChevronUp className="h-4 w-4 text-gray-400" />
                  ) : (
                    <ChevronDown className="h-4 w-4 text-gray-400" />
                  )}
                </button>

                {showOcrOptions && (
                  <div className="px-5 pb-5 border-t border-white/10">
                    <div className="pt-4">
                      <ProcessingOptions
                        onOptionsChange={setOcrOptions}
                        initialOptions={ocrOptions}
                        disabled={isSaving}
                        compact={true}
                        dark={true}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Visual Schema Editor */}
              <div className="bg-white/5 rounded-xl p-5 border border-white/10 max-h-[calc(100vh-280px)] overflow-y-auto">
                <SchemaEditor
                  fields={schemaFields}
                  onChange={setSchemaFields}
                  disabled={isSaving}
                />
              </div>
            </div>

            {/* Right Column - Test Panel */}
            <div className="xl:sticky xl:top-4">
              <div className="bg-white/5 rounded-xl border border-white/10 overflow-hidden">
                {/* Test Header */}
                <div className="px-5 py-4 border-b border-white/10 bg-white/5">
                  <h3 className="text-base font-semibold text-white flex items-center gap-2">
                    🧪 Tester l'extraction
                  </h3>
                  <p className="text-xs text-gray-400 mt-1">
                    Testez votre schéma avec un document PDF
                  </p>
                </div>

                <div className="p-5 space-y-5">
                  {/* Test with URL */}
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">
                      Via URL
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="url"
                        value={testUrl}
                        onChange={(e) => setTestUrl(e.target.value)}
                        className="flex-1 px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                        placeholder="https://example.com/document.pdf"
                      />
                      <button
                        onClick={testWithUrl}
                        disabled={isTesting || !testUrl}
                        className="px-4 py-2 rounded-lg bg-purple-500 text-white text-sm font-medium hover:bg-purple-600 transition disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {isTesting ? (
                          <span className="flex items-center gap-2">
                            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Test...
                          </span>
                        ) : 'Extraire'}
                      </button>
                    </div>
                  </div>

                  {/* Divider */}
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-px bg-white/10"></div>
                    <span className="text-xs text-gray-500">ou</span>
                    <div className="flex-1 h-px bg-white/10"></div>
                  </div>

                  {/* Test with File */}
                  <div>
                    <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">
                      Via fichier
                    </label>
                    <div className="flex gap-2">
                      <label className="flex-1 cursor-pointer">
                        <div className={`
                          px-3 py-2 rounded-lg border border-dashed text-sm transition
                          ${testFile
                            ? 'border-purple-500 bg-purple-500/10 text-purple-300'
                            : 'border-white/20 bg-white/5 text-gray-400 hover:border-white/30 hover:bg-white/10'
                          }
                        `}>
                          {testFile ? (
                            <span className="flex items-center gap-2">
                              <svg className="h-4 w-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                              {testFile.name}
                            </span>
                          ) : (
                            <span className="flex items-center gap-2">
                              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                              </svg>
                              Choisir un fichier PDF...
                            </span>
                          )}
                        </div>
                        <input
                          type="file"
                          accept=".pdf"
                          onChange={(e) => setTestFile(e.target.files?.[0] || null)}
                          className="hidden"
                        />
                      </label>
                      <button
                        onClick={testWithFile}
                        disabled={isTesting || !testFile}
                        className="px-4 py-2 rounded-lg bg-purple-500 text-white text-sm font-medium hover:bg-purple-600 transition disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                      >
                        {isTesting ? (
                          <span className="flex items-center gap-2">
                            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                            Test...
                          </span>
                        ) : 'Extraire'}
                      </button>
                    </div>
                  </div>

                  {/* Processing indicator - Shown during test */}
                  {isTesting && (
                    <div className="mt-4 rounded-lg bg-black/20 border border-white/10 p-4">
                      <div className="flex items-center gap-3">
                        <svg className="animate-spin h-5 w-5 text-purple-500" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        <span className="text-sm font-medium text-white">Extraction en cours...</span>
                        <span className="ml-auto text-xs font-mono text-purple-400 bg-purple-500/20 px-2 py-1 rounded">
                          ⏱ {elapsedTime.toFixed(1)}s
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Test Result */}
                  {testResult && (
                    <div className="mt-4 rounded-lg bg-black/20 border border-white/10 overflow-hidden">
                      <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between bg-white/5">
                        <span className={`px-2 py-1 text-xs rounded-full font-medium ${testResult.status === 'completed'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                          }`}>
                          {testResult.status === 'completed' ? '✓ Succès' : '✗ Erreur'}
                        </span>
                        {testResult.processing_time && (
                          <span className="text-xs text-gray-500">
                            ⏱ {testResult.processing_time.toFixed(2)}s
                          </span>
                        )}
                      </div>

                      {/* Show main steps summary (OCR and LLM aggregated) */}
                      {testSteps.length > 0 && (() => {
                        // Aggregate OCR steps (everything except LLM)
                        const ocrSteps = testSteps.filter(step =>
                          !(step.name || '').includes('LLM') &&
                          !(step.name || '').includes('Chargement')
                        )
                        const llmSteps = testSteps.filter(step =>
                          (step.name || '').includes('LLM')
                        )

                        const ocrDuration = ocrSteps.reduce((sum, step) => sum + (step.duration || 0), 0)
                        const llmDuration = llmSteps.reduce((sum, step) => sum + (step.duration || 0), 0)

                        const ocrCompleted = ocrSteps.every(step => step.status === 'completed')
                        const llmCompleted = llmSteps.every(step => step.status === 'completed')
                        const ocrFailed = ocrSteps.some(step => step.status === 'failed')
                        const llmFailed = llmSteps.some(step => step.status === 'failed')

                        return (
                          <div className="px-4 py-3 border-b border-white/10 bg-black/10">
                            <div className="flex items-center gap-6 text-sm">
                              <div className="flex items-center gap-2">
                                {ocrCompleted ? (
                                  <span className="text-green-400">✓</span>
                                ) : ocrFailed ? (
                                  <span className="text-red-400">✗</span>
                                ) : (
                                  <span className="text-gray-500">○</span>
                                )}
                                <span className="text-gray-300">🔍 Traitement OCR</span>
                                {ocrDuration > 0 && (
                                  <span className="text-gray-500 font-mono">({ocrDuration.toFixed(1)}s)</span>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                {llmCompleted ? (
                                  <span className="text-green-400">✓</span>
                                ) : llmFailed ? (
                                  <span className="text-red-400">✗</span>
                                ) : (
                                  <span className="text-gray-500">○</span>
                                )}
                                <span className="text-gray-300">🤖 Analyse LLM</span>
                                {llmDuration > 0 && (
                                  <span className="text-gray-500 font-mono">({llmDuration.toFixed(1)}s)</span>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })()}

                      <div className="p-4 max-h-80 overflow-auto">
                        {testResult.extracted_data && (
                          <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
                            {JSON.stringify(testResult.extracted_data, null, 2)}
                          </pre>
                        )}
                        {testResult.error_message && (
                          <p className="text-sm text-red-400">{testResult.error_message}</p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Empty State */}
                  {!testResult && !isTesting && (
                    <div className="text-center py-6 text-gray-500">
                      <svg className="h-12 w-12 mx-auto mb-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-sm">Testez votre extraction avec un document</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'api' && (
          <div className="max-w-4xl mx-auto">
            <h3 className="text-lg font-semibold text-white mb-6">Documentation API</h3>

            {/* API Key */}
            <div className="mb-8 p-4 rounded-lg bg-white/5 border border-white/10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Clé API</p>
                  <code className="text-purple-400 font-mono">{flow?.api_key}</code>
                </div>
                <button
                  onClick={copyApiKey}
                  className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Endpoint Documentation */}
            <div className="space-y-6">
              {/* Endpoint URL */}
              <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <p className="text-sm text-gray-400 mb-1">Endpoint</p>
                <p className="text-green-400 font-mono">POST {API_BASE_URL}/api/v1/extract/{flow?.api_key}</p>
              </div>

              <div>
                <h4 className="text-white font-medium mb-3">Mode 1 : Extraction via URL (JSON)</h4>
                <div className="p-4 rounded-lg bg-slate-800 font-mono text-sm">
                  <p className="text-gray-500">Content-Type: application/json</p>
                  <pre className="text-gray-300 mt-2">{`{
  "url": "https://example.com/document.pdf"
}`}</pre>
                </div>
              </div>

              <div>
                <h4 className="text-white font-medium mb-3">Mode 2 : Fichier binaire (octet-stream)</h4>
                <div className="p-4 rounded-lg bg-slate-800 font-mono text-sm">
                  <p className="text-gray-500">Content-Type: application/octet-stream</p>
                  <p className="text-gray-500">X-Filename: document.pdf</p>
                  <p className="text-gray-300 mt-2">Body: &lt;contenu binaire du fichier&gt;</p>
                </div>
              </div>

              <div>
                <h4 className="text-white font-medium mb-3">Mode 3 : Fichier multipart (form-data)</h4>
                <div className="p-4 rounded-lg bg-slate-800 font-mono text-sm">
                  <p className="text-gray-500">Content-Type: multipart/form-data</p>
                  <p className="text-gray-300 mt-2">file: &lt;document.pdf&gt;</p>
                </div>
              </div>

              <div>
                <h4 className="text-white font-medium mb-3">Exemples cURL</h4>
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-slate-800 font-mono text-sm text-gray-300 overflow-x-auto">
                    <p className="text-gray-500 mb-2"># Via URL (JSON)</p>
                    <pre>{`curl -X POST "${API_BASE_URL}/api/v1/extract/${flow?.api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com/invoice.pdf"}'`}</pre>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-800 font-mono text-sm text-gray-300 overflow-x-auto">
                    <p className="text-gray-500 mb-2"># Via fichier binaire</p>
                    <pre>{`curl -X POST "${API_BASE_URL}/api/v1/extract/${flow?.api_key}" \\
  -H "Content-Type: application/octet-stream" \\
  -H "X-Filename: invoice.pdf" \\
  --data-binary @invoice.pdf`}</pre>
                  </div>
                  <div className="p-4 rounded-lg bg-slate-800 font-mono text-sm text-gray-300 overflow-x-auto">
                    <p className="text-gray-500 mb-2"># Via multipart form-data</p>
                    <pre>{`curl -X POST "${API_BASE_URL}/api/v1/extract/${flow?.api_key}" \\
  -F "file=@invoice.pdf"`}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="max-w-4xl mx-auto">
            <h3 className="text-lg font-semibold text-white mb-6">Historique des exécutions</h3>

            {executions.length === 0 ? (
              <p className="text-gray-400">Aucune exécution pour le moment</p>
            ) : (
              <div className="space-y-3">
                {executions.map((exec) => (
                  <div key={exec.id} className="p-4 rounded-lg bg-white/5 border border-white/10">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <span className={`px-2 py-0.5 text-xs rounded-full ${exec.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                          exec.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                            'bg-yellow-500/20 text-yellow-400'
                          }`}>
                          {exec.status}
                        </span>
                        <span className="text-sm text-gray-400">
                          {exec.input_type === 'url' ? '🔗' : '📄'} {exec.input_source}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(exec.created_at).toLocaleString()}
                      </span>
                    </div>
                    {exec.processing_time && (
                      <p className="text-xs text-gray-500">
                        Temps: {exec.processing_time.toFixed(2)}s
                      </p>
                    )}
                    {exec.extracted_data && (
                      <details className="mt-2">
                        <summary className="text-sm text-purple-400 cursor-pointer">
                          Voir le résultat
                        </summary>
                        <pre className="mt-2 text-xs text-gray-300 overflow-x-auto p-2 bg-black/20 rounded">
                          {JSON.stringify(exec.extracted_data, null, 2)}
                        </pre>
                      </details>
                    )}
                    {exec.error_message && (
                      <p className="mt-2 text-sm text-red-400">{exec.error_message}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
