import React from 'react'

const NotFound: React.FC = () => {
  return (
    <div className="text-center">
      <h2 className="text-4xl font-bold text-gray-900 mb-4">
        404
      </h2>
      <h3 className="text-2xl font-semibold text-gray-700 mb-4">
        Page Not Found
      </h3>
      <p className="text-gray-600 mb-8">
        The page you're looking for doesn't exist.
      </p>
      
      <div className="space-x-4">
        <a 
          href="/" 
          className="btn-primary px-4 py-2"
        >
          Go Home
        </a>
        <a 
          href="/process" 
          className="btn-outline px-4 py-2"
        >
          Process Document
        </a>
      </div>
    </div>
  )
}

export default NotFound 