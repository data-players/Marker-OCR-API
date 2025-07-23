import React from 'react'
import { useParams } from 'react-router-dom'

const JobStatus: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>()

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">
        Job Status
      </h2>
      
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600 mb-4">
          Job ID: <span className="font-mono text-sm">{jobId}</span>
        </p>
        
        <div className="border border-gray-200 rounded p-4">
          <p className="text-gray-500">
            Job status tracking functionality will be implemented here
          </p>
        </div>
      </div>
    </div>
  )
}

export default JobStatus 