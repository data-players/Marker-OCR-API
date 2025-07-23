import { useState } from 'react'
import './App.css'

function App() {
  return (
    <div className="App" data-testid="app">
      <header className="App-header">
        <h1>Marker OCR API</h1>
        <p>Document OCR Processing Service</p>
      </header>
      <main>
        <div className="upload-section">
          <h2>Upload Document</h2>
          <p>Upload your PDF document for OCR processing</p>
          <div className="upload-placeholder">
            Upload functionality coming soon...
          </div>
        </div>
      </main>
    </div>
  )
}

export default App 