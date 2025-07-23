import React, { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import toast, { Toaster } from 'react-hot-toast'

import Layout from '@/components/Layout'
import ModelLoadingScreen from '@/components/ModelLoadingScreen'
import Home from '@/pages/Home'
import ProcessDocument from '@/pages/ProcessDocument'  
import JobStatus from '@/pages/JobStatus'
import NotFound from '@/pages/NotFound'

function App() {
  const [modelsReady, setModelsReady] = useState(false)
  const [isCheckingModels, setIsCheckingModels] = useState(true)

  useEffect(() => {
    // Check initial model status
    const checkInitialModelStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/health/models')
        const status = await response.json()
        
        if (status.models_loaded && status.status === 'ready') {
          setModelsReady(true)
        }
      } catch (error) {
        console.error('Failed to check initial model status:', error)
        // Continue to show loading screen which will handle the error
      } finally {
        setIsCheckingModels(false)
      }
    }

    checkInitialModelStatus()
  }, [])

  const handleModelsReady = () => {
    setModelsReady(true)
    toast.success('Modèles IA chargés avec succès !', {
      duration: 3000,
      icon: '🤖'
    })
  }

  // Show loading screen while checking or if models are not ready
  if (isCheckingModels || !modelsReady) {
    return <ModelLoadingScreen onModelsReady={handleModelsReady} />
  }

  // Show main app when models are ready
  return (
    <div className="min-h-screen bg-gray-50">
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/process" element={<ProcessDocument />} />
          <Route path="/job/:jobId" element={<JobStatus />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
      
      {/* Global toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            style: {
              background: '#059669',
            },
          },
          error: {
            style: {
              background: '#DC2626',
            },
          },
        }}
      />
    </div>
  )
}

export default App 