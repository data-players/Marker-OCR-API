import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import toast, { Toaster } from 'react-hot-toast'

import { AuthProvider, useAuth } from '@/contexts/AuthContext'
import ModelLoadingScreen from '@/components/ModelLoadingScreen'

// Public pages
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import ApiDocs from '@/pages/ApiDocs'
import NotFound from '@/pages/NotFound'

// Protected pages
import Dashboard from '@/pages/Dashboard'
import Workspace from '@/pages/Workspace'
import FlowEditor from '@/pages/FlowEditor'

// Protected route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-purple-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// Public route that redirects if authenticated
function PublicOnlyRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-purple-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    )
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

function AppContent() {
  const [modelsReady, setModelsReady] = useState(false)
  const [isCheckingModels, setIsCheckingModels] = useState(true)
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    const checkInitialModelStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health/models`)
        const status = await response.json()
        
        if (status.models_loaded && status.status === 'ready') {
          setModelsReady(true)
        }
      } catch (error) {
        console.error('Failed to check initial model status:', error)
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        {/* Auth routes (public only) */}
        <Route path="/login" element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        } />
        <Route path="/register" element={
          <PublicOnlyRoute>
            <Register />
          </PublicOnlyRoute>
        } />
        
        {/* Protected routes (require auth) */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/workspace/:workspaceId" element={
          <ProtectedRoute>
            <Workspace />
          </ProtectedRoute>
        } />
        <Route path="/workspace/:workspaceId/flow/:flowId" element={
          <ProtectedRoute>
            <FlowEditor />
          </ProtectedRoute>
        } />
        
        {/* Public routes */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/api" element={<ApiDocs />} />
        <Route path="/api/*" element={<ApiDocs />} />
        
        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
      
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

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
