import React, { useState } from 'react'
import { Settings, Image, FileText, Globe } from 'lucide-react'
import { ProcessingOptions as ProcessingOptionsType } from '@/services/api'

interface ProcessingOptionsProps {
  onOptionsChange: (options: Partial<ProcessingOptionsType>) => void
  initialOptions?: Partial<ProcessingOptionsType>
  disabled?: boolean
  compact?: boolean
  dark?: boolean  // Dark theme support for FlowEditor
}

const ProcessingOptions: React.FC<ProcessingOptionsProps> = ({
  onOptionsChange,
  initialOptions,
  disabled = false,
  compact = false,
  dark = false
}) => {
  // Theme-aware class names
  const labelClass = dark ? 'text-gray-300' : 'text-gray-700'
  const textClass = dark ? 'text-gray-300' : 'text-gray-700'
  const descClass = dark ? 'text-gray-400' : 'text-gray-600'
  const borderClass = dark ? 'border-white/20' : 'border-gray-200'
  const borderHoverClass = dark ? 'hover:border-white/30' : 'hover:border-gray-300'
  const selectedBorderClass = dark ? 'border-purple-500 bg-purple-500/20' : 'border-blue-500 bg-blue-50'
  const inputBgClass = dark ? 'bg-white/10 border-white/20 text-white' : 'border-gray-300'
  const checkboxClass = dark ? 'text-purple-500' : 'text-blue-600'
  const [options, setOptions] = useState<Partial<ProcessingOptionsType>>({
    output_format: 'markdown',
    force_ocr: false,
    extract_images: false,
    paginate_output: false,
    language: 'auto',
    ...initialOptions,
  })

  // Sync with parent when initialOptions change
  React.useEffect(() => {
    if (initialOptions) {
      setOptions(prev => ({ ...prev, ...initialOptions }))
    }
  }, [initialOptions])

  const updateOption = <K extends keyof ProcessingOptionsType>(
    key: K,
    value: ProcessingOptionsType[K]
  ) => {
    const newOptions = { ...options, [key]: value }
    setOptions(newOptions)
    onOptionsChange(newOptions)
  }

  const content = (
    <div className="space-y-6">
      {/* Output Format */}
      <div>
        <label className={`block text-sm font-medium ${labelClass} mb-3`}>
          Output Format
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { value: 'json', label: 'JSON', desc: 'Structured data format' },
            { value: 'markdown', label: 'Markdown', desc: 'Human-readable text' },
          ].map(({ value, label, desc }) => (
            <button
              key={value}
              onClick={() => updateOption('output_format', value as any)}
              disabled={disabled}
              className={`
                  p-3 border-2 rounded-lg text-left transition-colors
                  ${options.output_format === value
                  ? selectedBorderClass
                  : `${borderClass} ${borderHoverClass}`
                }
                  ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
            >
              <div className={`font-medium ${textClass}`}>{label}</div>
              <p className={`text-sm ${descClass}`}>{desc}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Advanced Options */}
      <div>
        <label className={`block text-sm font-medium ${labelClass} mb-3`}>
          Advanced Options
        </label>
        <div className="space-y-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={options.force_ocr}
              onChange={(e) => updateOption('force_ocr', e.target.checked)}
              disabled={disabled}
              className={`h-4 w-4 ${checkboxClass} rounded border-gray-300 focus:ring-purple-500`}
            />
            <span className={`ml-3 text-sm ${textClass}`}>
              Force OCR (even for text-based PDFs)
            </span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={options.extract_images}
              onChange={(e) => updateOption('extract_images', e.target.checked)}
              disabled={disabled}
              className={`h-4 w-4 ${checkboxClass} rounded border-gray-300 focus:ring-purple-500`}
            />
            <span className={`ml-3 text-sm ${textClass} flex items-center`}>
              <Image className="h-4 w-4 mr-1" />
              Extract images
            </span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={options.paginate_output}
              onChange={(e) => updateOption('paginate_output', e.target.checked)}
              disabled={disabled}
              className={`h-4 w-4 ${checkboxClass} rounded border-gray-300 focus:ring-purple-500`}
            />
            <span className={`ml-3 text-sm ${textClass} flex items-center`}>
              <FileText className="h-4 w-4 mr-1" />
              Add page separators in output
            </span>
          </label>
        </div>
      </div>

      {/* Language */}
      <div>
        <label className={`block text-sm font-medium ${labelClass} mb-3`}>
          <Globe className="h-4 w-4 inline mr-1" />
          Language
        </label>
        <select
          value={options.language}
          onChange={(e) => updateOption('language', e.target.value)}
          disabled={disabled}
          className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 ${inputBgClass}`}
        >
          <option value="auto">Auto-detect</option>
          <option value="en">English</option>
          <option value="fr">French</option>
          <option value="es">Spanish</option>
          <option value="de">German</option>
          <option value="it">Italian</option>
          <option value="pt">Portuguese</option>
          <option value="zh">Chinese</option>
          <option value="ja">Japanese</option>
          <option value="ko">Korean</option>
        </select>
      </div>
    </div>
  )

  if (compact) {
    return content
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center mb-6">
        <Settings className="h-5 w-5 text-gray-600 mr-2" />
        <h3 className="text-lg font-semibold text-gray-900">OCR Options</h3>
      </div>
      {content}
    </div>
  )
}

export default ProcessingOptions 