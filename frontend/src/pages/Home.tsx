import React from 'react'

const Home: React.FC = () => {
  return (
    <div className="text-center">
      <h2 className="text-3xl font-bold text-gray-900 mb-4">
        Welcome to Marker OCR API
      </h2>
      <p className="text-lg text-gray-600 mb-8">
        Convert PDF documents to structured JSON and Markdown with advanced OCR processing
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">Upload Documents</h3>
          <p className="text-gray-600">Securely upload PDF files for processing</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">Advanced Processing</h3>
          <p className="text-gray-600">Multiple processing options with OCR support</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">Multiple Formats</h3>
          <p className="text-gray-600">Get results in JSON or Markdown format</p>
        </div>
      </div>
      
      <div className="mt-8">
        <a 
          href="/process" 
          className="btn-primary px-6 py-3 text-lg"
        >
          Start Processing
        </a>
      </div>
    </div>
  )
}

export default Home 