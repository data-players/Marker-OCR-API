import { useEffect } from 'react'

/**
 * Redirect to backend API documentation
 */
export default function ApiDocs() {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    // Redirect to backend API docs
    window.location.href = `${API_BASE_URL}/docs`
  }, [])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Redirection vers la documentation de l'API...</p>
        <p className="text-sm text-gray-400 mt-2">
          <a 
            href={`${API_BASE_URL}/docs`}
            className="text-blue-500 hover:underline"
          >
            Cliquez ici si la redirection ne fonctionne pas
          </a>
        </p>
      </div>
    </div>
  )
}

