import React, { useState } from 'react'
import { CheckCircle, Circle, Loader, XCircle, ChevronDown, ChevronUp } from 'lucide-react'

export interface SubStep {
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  start_time?: number
  end_time?: number
  duration?: number
}

export interface ProcessingStep {
  name: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  start_time?: number
  end_time?: number
  duration?: number
  sub_steps?: string[]
  sub_steps_detailed?: SubStep[]
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
              
              {/* Show all sub-steps (using detailed sub-steps if available, otherwise fallback to simple list) */}
              {step.sub_steps_detailed && step.sub_steps_detailed.length > 0 ? (
                <div className="mt-3 ml-8 space-y-1.5">
                  {/* Sort sub-steps by start_time to ensure consistent order for dynamic additions */}
                  {(() => {
                    const sortedSubSteps = [...step.sub_steps_detailed].sort((a, b) => {
                      // Sort by start_time if available, otherwise by index
                      if (a.start_time && b.start_time) {
                        return a.start_time - b.start_time
                      }
                      if (a.start_time) return -1
                      if (b.start_time) return 1
                      return 0
                    })
                    
                    return sortedSubSteps.map((subStep, idx) => {
                      const isCurrentStep = subStep.status === 'in_progress'
                      const isCompleted = subStep.status === 'completed'
                      const isPending = subStep.status === 'pending'
                      
                      // Use a unique key based on name and start_time to handle dynamic additions
                      // This ensures React properly tracks sub-steps added dynamically by Marker's log handler
                      const uniqueKey = subStep.start_time 
                        ? `${subStep.name}-${subStep.start_time}` 
                        : `${subStep.name}-${idx}`
                      
                      return (
                        <div 
                          key={uniqueKey}
                          className={`text-xs flex items-center justify-between gap-4 transition-all duration-500 ease-in-out ${
                            isCurrentStep 
                              ? 'text-blue-600 font-medium transform scale-105 animate-fadeIn' 
                              : isCompleted 
                              ? 'text-gray-700' 
                              : 'text-gray-400'
                          } ${
                            isCompleted && idx > 0 && sortedSubSteps[idx - 1]?.status === 'in_progress'
                              ? 'animate-slideIn' 
                              : ''
                          }`}
                      >
                        <div className="flex items-center flex-1 min-w-0">
                          {isCurrentStep ? (
                            <Loader className="h-3.5 w-3.5 text-blue-500 mr-2 animate-spin flex-shrink-0" />
                          ) : isCompleted ? (
                            <CheckCircle className="h-3.5 w-3.5 text-green-500 mr-2 flex-shrink-0" />
                          ) : (
                            <Circle className="h-3.5 w-3.5 text-gray-300 mr-2 flex-shrink-0" />
                          )}
                          <span className={isCurrentStep ? 'font-medium' : ''}>{subStep.name}</span>
                        </div>
                        
                        {/* Show duration for completed and in-progress sub-steps */}
                        {subStep.duration !== undefined && subStep.duration > 0 && (
                          <span className={`text-xs font-mono px-2 py-0.5 rounded flex-shrink-0 ${
                            isCompleted 
                              ? 'text-green-600 bg-green-50' 
                              : isCurrentStep 
                              ? 'text-blue-600 bg-blue-50 animate-pulse' 
                              : ''
                          }`}>
                            {formatDuration(subStep.duration)}
                            {isCurrentStep && '...'}
                          </span>
                        )}
                      </div>
                      )
                    })
                  })()}
                </div>
              ) : step.sub_steps && step.sub_steps.length > 0 ? (
                // Fallback to simple sub-steps list (backward compatibility)
                <div className="mt-3 ml-8 space-y-1.5">
                  {step.sub_steps.map((subStep, idx) => {
                    const isLastStep = idx === step.sub_steps!.length - 1
                    const isCurrentStep = step.status === 'in_progress' && 
                                         (isLastStep || step.current_sub_step === subStep)
                    const isCompleted = step.status === 'completed' || 
                                       (step.status === 'in_progress' && !isCurrentStep)
                    
                    return (
                      <div 
                        key={`${subStep}-${idx}`}
                        className={`text-xs flex items-center transition-all duration-500 ease-in-out ${
                          isCurrentStep 
                            ? 'text-blue-600 font-medium transform scale-105 animate-fadeIn' 
                            : isCompleted 
                            ? 'text-gray-700' 
                            : 'text-gray-400'
                        }`}
                      >
                        {isCurrentStep ? (
                          <Loader className="h-3.5 w-3.5 text-blue-500 mr-2 animate-spin flex-shrink-0" />
                        ) : isCompleted ? (
                          <CheckCircle className="h-3.5 w-3.5 text-green-500 mr-2 flex-shrink-0" />
                        ) : (
                          <Circle className="h-3.5 w-3.5 text-gray-300 mr-2 flex-shrink-0" />
                        )}
                        <span className={isCurrentStep ? 'font-medium' : ''}>{subStep}</span>
                      </div>
                    )
                  })}
                </div>
              ) : null}
              
              {/* Show current sub-step if no sub_steps list exists yet */}
              {step.status === 'in_progress' && 
               step.current_sub_step && 
               (!step.sub_steps_detailed || step.sub_steps_detailed.length === 0) &&
               (!step.sub_steps || step.sub_steps.length === 0) && (
                <div className="mt-2 ml-8 text-xs text-blue-600 font-medium flex items-center">
                  <Loader className="h-3.5 w-3.5 text-blue-500 mr-2 animate-spin flex-shrink-0" />
                  <span>{step.current_sub_step}</span>
                </div>
              )}
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

