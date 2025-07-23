import React, { useState, useEffect } from 'react'
import { 
  Loader, 
  CheckCircle, 
  XCircle, 
  Brain,
  Download,
  RefreshCw
} from 'lucide-react'
import { apiService } from '@/services/api'

interface ModelStatus {
  status: 'loading' | 'ready' | 'error'
  progress: number
  message: string
  models_loaded: boolean
  error?: string
}

interface ModelLoadingScreenProps {
  onModelsReady: () => void
}

const ModelLoadingScreen: React.FC<ModelLoadingScreenProps> = ({ onModelsReady }) => {
  const [modelStatus, setModelStatus] = useState<ModelStatus>({
    status: 'loading',
    progress: 0,
    message: 'Initializing...',
    models_loaded: false
  })
  const [isRetrying, setIsRetrying] = useState(false)

  useEffect(() => {
    let interval: NodeJS.Timeout

    const checkModelStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/health/models')
        const status = await response.json()
        setModelStatus(status)

        if (status.models_loaded && status.status === 'ready') {
          if (interval) clearInterval(interval)
          setTimeout(() => onModelsReady(), 1000) // Small delay for UX
        }
      } catch (error) {
        console.error('Failed to check model status:', error)
        setModelStatus(prev => ({
          ...prev,
          status: 'error',
          message: 'Failed to connect to backend',
          error: 'Connection failed'
        }))
      }
    }

    // Check immediately
    checkModelStatus()

    // Poll every 2 seconds
    interval = setInterval(checkModelStatus, 2000)

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [onModelsReady])

  const handleRetry = async () => {
    setIsRetrying(true)
    try {
      await fetch('http://localhost:8000/api/v1/health/models/reload', { 
        method: 'POST' 
      })
      setModelStatus({
        status: 'loading',
        progress: 0,
        message: 'Retrying model loading...',
        models_loaded: false
      })
    } catch (error) {
      console.error('Failed to retry model loading:', error)
    } finally {
      setIsRetrying(false)
    }
  }

  const getStatusIcon = () => {
    switch (modelStatus.status) {
      case 'ready':
        return <CheckCircle className="h-16 w-16 text-green-500" />
      case 'error':
        return <XCircle className="h-16 w-16 text-red-500" />
      default:
        return <Loader className="h-16 w-16 text-blue-500 animate-spin" />
    }
  }

  const getStatusColor = () => {
    switch (modelStatus.status) {
      case 'ready':
        return 'bg-green-50 border-green-200'
      case 'error':
        return 'bg-red-50 border-red-200'
      default:
        return 'bg-blue-50 border-blue-200'
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className={`max-w-md w-full bg-white rounded-lg shadow-lg border-2 p-8 text-center ${getStatusColor()}`}>
        {/* Header */}
        <div className="mb-6">
          <Brain className="h-12 w-12 mx-auto mb-4 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Marker OCR API
          </h1>
          <p className="text-gray-600">
            Initialisation des modèles d'IA
          </p>
        </div>

        {/* Status Icon */}
        <div className="mb-6">
          {getStatusIcon()}
        </div>

        {/* Status Message */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            {modelStatus.status === 'ready' ? 'Prêt !' : 
             modelStatus.status === 'error' ? 'Erreur' : 'Chargement...'}
          </h2>
          <p className="text-gray-600 text-sm mb-4">
            {modelStatus.message}
          </p>
          
          {modelStatus.status === 'error' && modelStatus.error && (
            <div className="bg-red-100 border border-red-300 rounded p-3 mb-4">
              <p className="text-red-800 text-sm">
                {modelStatus.error}
              </p>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        {modelStatus.status === 'loading' && (
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>Progression</span>
              <span>{modelStatus.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-500 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${modelStatus.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Actions */}
        {modelStatus.status === 'error' && (
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="flex items-center justify-center w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRetrying ? (
              <Loader className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Réessayer
          </button>
        )}

        {modelStatus.status === 'ready' && (
          <div className="text-green-600 font-medium">
            <CheckCircle className="h-5 w-5 inline mr-2" />
            Tous les modèles sont chargés !
          </div>
        )}

        {/* Info */}
        <div className="mt-8 text-xs text-gray-500 space-y-1">
          <p>
            {modelStatus.status === 'loading' && modelStatus.progress < 50 ? (
              <>
                <Download className="h-3 w-3 inline mr-1" />
                Première utilisation : téléchargement des modèles IA...
              </>
            ) : modelStatus.status === 'loading' ? (
              <>
                <Brain className="h-3 w-3 inline mr-1" />
                Initialisation des modèles...
              </>
            ) : null}
          </p>
          <p>Cette opération peut prendre quelques minutes lors du premier démarrage.</p>
        </div>
      </div>
    </div>
  )
}

export default ModelLoadingScreen 