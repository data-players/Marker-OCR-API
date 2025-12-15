import React, { useState } from 'react'
import { Settings, Image, FileText, Globe } from 'lucide-react'
import { ProcessingOptions as ProcessingOptionsType } from '@/services/api'

interface ProcessingOptionsProps {
  onOptionsChange: (options: Partial<ProcessingOptionsType>) => void
  disabled?: boolean
}

const ProcessingOptions: React.FC<ProcessingOptionsProps> = ({ 
  onOptionsChange, 
  disabled = false 
}) => {
  const [options, setOptions] = useState<Partial<ProcessingOptionsType>>({
    output_format: 'markdown',
    force_ocr: false,
    extract_images: false,
    paginate_output: false,
    language: 'auto',
  })

  const updateOption = <K extends keyof ProcessingOptionsType>(
    key: K, 
    value: ProcessingOptionsType[K]
  ) => {
    const newOptions = { ...options, [key]: value }
    setOptions(newOptions)
    onOptionsChange(newOptions)
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center mb-6">
        <Settings className="h-5 w-5 text-gray-600 mr-2" />
        <h3 className="text-lg font-semibold text-gray-900">Processing Options</h3>
      </div>

      <div className="space-y-6">
        {/* Output Format */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Output Format
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { value: 'json', label: 'JSON', desc: 'Structured data format' },
              { value: 'markdown', label: 'Markdown', desc: 'Human-readable text' },
              { value: 'both', label: 'Both', desc: 'JSON + Markdown' },
            ].map(({ value, label, desc }) => (
              <button
                key={value}
                onClick={() => updateOption('output_format', value as any)}
                disabled={disabled}
                className={`
                  p-3 border-2 rounded-lg text-left transition-colors
                  ${options.output_format === value 
                    ? 'border-blue-500 bg-blue-50' 
                    : 'border-gray-200 hover:border-gray-300'
                  }
                  ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                `}
              >
                <div className="font-medium">{label}</div>
                <p className="text-sm text-gray-600">{desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Advanced Options */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Advanced Options
          </label>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={options.force_ocr}
                onChange={(e) => updateOption('force_ocr', e.target.checked)}
                disabled={disabled}
                className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
              <span className="ml-3 text-sm text-gray-700">
                Force OCR (even for text-based PDFs)
              </span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={options.extract_images}
                onChange={(e) => updateOption('extract_images', e.target.checked)}
                disabled={disabled}
                className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
              <span className="ml-3 text-sm text-gray-700 flex items-center">
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
                className="h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
              <span className="ml-3 text-sm text-gray-700 flex items-center">
                <FileText className="h-4 w-4 mr-1" />
                Add page separators in output
              </span>
            </label>
          </div>
        </div>

        {/* Language */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            <Globe className="h-4 w-4 inline mr-1" />
            Language
          </label>
          <select
            value={options.language}
            onChange={(e) => updateOption('language', e.target.value)}
            disabled={disabled}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
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
    </div>
  )
}

export default ProcessingOptions 