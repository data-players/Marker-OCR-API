import React, { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

interface Flow {
  id: string
  workspace_id: string
  name: string
  description: string | null
  api_key: string
  extraction_schema: Record<string, any>
  introduction: string
  ocr_options: Record<string, any>
  is_active: boolean
  created_at: string
  execution_count: number
}

interface Workspace {
  id: string
  name: string
  description: string | null
}

export default function WorkspacePage() {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [flows, setFlows] = useState<Flow[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newFlowName, setNewFlowName] = useState('')
  const [newFlowDescription, setNewFlowDescription] = useState('')
  const [isCreating, setIsCreating] = useState(false)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchWorkspaceAndFlows()
  }, [workspaceId])

  const fetchWorkspaceAndFlows = async () => {
    try {
      // Fetch workspace
      const wsResponse = await fetch(`${API_BASE_URL}/api/v1/workspaces/${workspaceId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (!wsResponse.ok) {
        navigate('/dashboard')
        return
      }
      
      const wsData = await wsResponse.json()
      setWorkspace(wsData)

      // Fetch flows
      const flowsResponse = await fetch(`${API_BASE_URL}/api/v1/workspaces/${workspaceId}/flows`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (flowsResponse.ok) {
        const flowsData = await flowsResponse.json()
        setFlows(flowsData.flows)
      }
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setIsLoading(false)
    }
  }

  const createFlow = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsCreating(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/workspaces/${workspaceId}/flows`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newFlowName,
          description: newFlowDescription || null
        })
      })

      if (response.ok) {
        const flow = await response.json()
        setFlows([flow, ...flows])
        setShowCreateModal(false)
        setNewFlowName('')
        setNewFlowDescription('')
        toast.success('Flow créé !')
        navigate(`/workspace/${workspaceId}/flow/${flow.id}`)
      }
    } catch (error) {
      toast.error('Erreur lors de la création')
    } finally {
      setIsCreating(false)
    }
  }

  const deleteFlow = async (flowId: string) => {
    if (!confirm('Supprimer ce flow et tout son historique ?')) return

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/workspaces/${workspaceId}/flows/${flowId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        setFlows(flows.filter(f => f.id !== flowId))
        toast.success('Flow supprimé')
      }
    } catch (error) {
      toast.error('Erreur lors de la suppression')
    }
  }

  const copyApiKey = (apiKey: string) => {
    navigator.clipboard.writeText(apiKey)
    toast.success('Clé API copiée !')
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
            <Link to="/dashboard" className="text-gray-400 hover:text-white transition">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-xl font-bold text-white">{workspace?.name}</h1>
          </div>
          <button
            onClick={logout}
            className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition"
          >
            Déconnexion
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-white">Flows d'extraction</h2>
            <p className="text-gray-400 mt-1">
              {workspace?.description || 'Configurez vos pipelines OCR avec schéma personnalisé'}
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 text-white font-medium hover:from-purple-600 hover:to-pink-600 transition flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Nouveau Flow</span>
          </button>
        </div>

        {/* Flows List */}
        {flows.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/5 mb-4">
              <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-white mb-2">Aucun flow</h3>
            <p className="text-gray-400 mb-6">Créez votre premier flow d'extraction</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 rounded-lg bg-purple-500 text-white hover:bg-purple-600 transition"
            >
              Créer un flow
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {flows.map((flow) => (
              <div
                key={flow.id}
                className="bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition"
              >
                <div className="flex items-start justify-between">
                  <Link to={`/workspace/${workspaceId}/flow/${flow.id}`} className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">{flow.name}</h3>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${flow.is_active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                        {flow.is_active ? 'Actif' : 'Inactif'}
                      </span>
                    </div>
                    <p className="text-gray-400 text-sm mb-3">
                      {flow.description || 'Aucune description'}
                    </p>
                  </Link>
                  <button
                    onClick={() => deleteFlow(flow.id)}
                    className="p-2 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
                
                {/* API Key */}
                <div className="flex items-center space-x-4 pt-4 border-t border-white/10">
                  <div className="flex-1">
                    <p className="text-xs text-gray-500 mb-1">Clé API</p>
                    <code className="text-sm text-purple-400 font-mono">{flow.api_key}</code>
                  </div>
                  <button
                    onClick={() => copyApiKey(flow.api_key)}
                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition"
                    title="Copier la clé"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                  <span className="text-sm text-gray-500">
                    {flow.execution_count} exécution{flow.execution_count !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md mx-4 border border-white/10">
            <h3 className="text-xl font-bold text-white mb-4">Nouveau Flow</h3>
            <form onSubmit={createFlow}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-300 mb-2">Nom</label>
                <input
                  type="text"
                  value={newFlowName}
                  onChange={(e) => setNewFlowName(e.target.value)}
                  required
                  className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Extraction factures"
                />
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
                <textarea
                  value={newFlowDescription}
                  onChange={(e) => setNewFlowDescription(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Extrait les informations des factures..."
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white transition"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="px-4 py-2 rounded-lg bg-purple-500 text-white hover:bg-purple-600 transition disabled:opacity-50"
                >
                  {isCreating ? 'Création...' : 'Créer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
