import React, { useState } from 'react'
import { CheckCircle, Circle, Loader, XCircle, ChevronDown, ChevronUp } from 'lucide-react'

export interface ProcessingStep {
  name: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  start_time?: number
  end_time?: number
  duration?: number
  // Legacy fields kept for backward compatibility but not used
  sub_steps?: string[]
  sub_steps_detailed?: any[]
  current_sub_step?: string
}

interface StepProgressProps {
  steps: ProcessingStep[]
  isCompleted?: boolean // Indicates if the entire job is completed
}

const StepProgress: React.FC<StepProgressProps> = ({ steps, isCompleted = false }) => {
  // Accordion state: collapsed by default when completed
  const [isExpanded, setIsExpanded] = useState(!isCompleted)
  
  // Update expanded state when completion status changes
  React.useEffect(() => {
    if (isCompleted) {
      setIsExpanded(false) // Collapse when completed
    } else {
      setIsExpanded(true) // Expand when processing
    }
  }, [isCompleted])
  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
      case 'in_progress':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin flex-shrink-0" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
      case 'pending':
      default:
        return <Circle className="h-5 w-5 text-gray-300 flex-shrink-0" />
    }
  }

  const getStepColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200'
      case 'in_progress':
        return 'bg-blue-50 border-blue-200'
      case 'failed':
        return 'bg-red-50 border-red-200'
      case 'pending':
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const formatDuration = (duration?: number) => {
    if (duration === undefined || duration === null) return null
    
    // Handle very small durations (< 1ms)
    if (duration < 0.001) {
      return '<1ms'
    }
    
    if (duration < 1) {
      return `${Math.round(duration * 1000)}ms`
    } else if (duration < 60) {
      return `${duration.toFixed(2)}s`
    } else {
      const minutes = Math.floor(duration / 60)
      const seconds = Math.round(duration % 60)
      return `${minutes}m ${seconds}s`
    }
  }

  const allStepsCompleted = steps.every(s => s.status === 'completed' || s.status === 'failed')
  const showAccordion = isCompleted || allStepsCompleted

  return (
    <div className="space-y-3">
      {/* Accordion header - clickable when completed */}
      {showAccordion ? (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center justify-between w-full text-left mb-4 p-2 -m-2 rounded-lg hover:bg-gray-50 transition-colors gap-4"
          aria-expanded={isExpanded}
          aria-label={isExpanded ? 'Masquer les étapes' : 'Afficher les étapes'}
        >
          <h3 className="font-medium text-gray-900 flex-shrink-0">Processing Steps</h3>
          <div className="flex items-center gap-2 flex-shrink-0">
            {allStepsCompleted && (
              <span className="text-xs font-mono text-green-700 bg-green-100 px-2 py-1 rounded">
                {formatDuration(steps.reduce((sum, s) => sum + (s.duration || 0), 0))}
              </span>
            )}
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-gray-500 flex-shrink-0" />
            ) : (
              <ChevronDown className="h-5 w-5 text-gray-500 flex-shrink-0" />
            )}
          </div>
        </button>
      ) : (
        <h3 className="font-medium text-gray-900 mb-4">Processing Steps</h3>
      )}
      
      {/* Steps container with accordion animation */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? 'max-h-[5000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
        style={{
          display: isExpanded ? 'block' : 'none'
        }}
      >
        <div className="space-y-3">
          {steps.map((step, index) => {
            // Debug: log step data to understand why durations aren't showing
            if (step.status === 'completed' || step.status === 'in_progress') {
              console.log(`[StepProgress] Step ${step.name}:`, {
                status: step.status,
                duration: step.duration,
                start_time: step.start_time,
                end_time: step.end_time,
                hasDuration: step.duration !== undefined && step.duration !== null
              })
            }
            return (
        <div
          key={index}
          className={`border rounded-lg p-4 transition-all duration-300 ${getStepColor(step.status)}`}
        >
          <div className="flex items-start">
            <div className="mt-0.5">
              {getStepIcon(step.status)}
            </div>
            
            <div className="ml-3 flex-1 min-w-0">
              <div className="flex items-center justify-between gap-4">
                <h4 className="font-medium text-gray-900 text-sm flex-shrink-0">
                  {step.name}
                </h4>
                
                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Show duration for completed and in-progress steps */}
                  {step.status === 'completed' && (
                    step.duration !== undefined && step.duration !== null ? (
                      <span className="text-xs font-mono text-green-700 bg-green-100 px-2 py-1 rounded">
                        {formatDuration(step.duration)}
                      </span>
                    ) : (
                      <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        &lt;1ms
                      </span>
                    )
                  )}
                  {step.status === 'in_progress' && (
                    step.duration !== undefined && step.duration !== null && step.duration > 0 ? (
                      <span className="text-xs font-mono text-blue-700 bg-blue-100 px-2 py-1 rounded animate-pulse">
                        {formatDuration(step.duration)}...
                      </span>
                    ) : (
                      <span className="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded animate-pulse">
                        In progress...
                      </span>
                    )
                  )}
                  
                  {step.status === 'failed' && (
                    <span className="text-xs text-red-700 bg-red-100 px-2 py-1 rounded">
                      Failed
                    </span>
                  )}
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mt-1">
                {step.description}
              </p>
            </div>
          </div>
          </div>
            )
          })}
        
        {/* Summary */}
        {steps.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-4">
                <span className="text-gray-600">
                  <span className="font-medium text-green-600">
                    {steps.filter(s => s.status === 'completed').length}
                  </span>
                  {' '}completed
                </span>
                
                {steps.some(s => s.status === 'in_progress') && (
                  <span className="text-gray-600">
                    <span className="font-medium text-blue-600">
                      {steps.filter(s => s.status === 'in_progress').length}
                    </span>
                    {' '}in progress
                  </span>
                )}
                
                {steps.some(s => s.status === 'failed') && (
                  <span className="text-gray-600">
                    <span className="font-medium text-red-600">
                      {steps.filter(s => s.status === 'failed').length}
                    </span>
                    {' '}failed
                  </span>
                )}
              </div>
              
              {/* Total time */}
              {steps.every(s => s.status === 'completed') && (
                <span className="text-gray-600">
                  Total:{' '}
                  <span className="font-medium font-mono text-gray-900">
                    {formatDuration(
                      steps.reduce((sum, s) => sum + (s.duration || 0), 0)
                    )}
                  </span>
                </span>
              )}
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  )
}

export default StepProgress

