import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import { Copy, Check } from 'lucide-react'

interface MarkdownPreviewProps {
  content: string
  className?: string
}

const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({ content, className = '' }) => {
  const [copied, setCopied] = React.useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  return (
    <div className={`relative ${className}`}>
      {/* Header avec bouton copier */}
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-200">
        <h4 className="font-medium text-gray-900">Preview Markdown</h4>
        <button
          onClick={handleCopy}
          className="flex items-center px-2 py-1 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
          title="Copier le markdown"
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 mr-1 text-green-600" />
              Copié !
            </>
          ) : (
            <>
              <Copy className="h-4 w-4 mr-1" />
              Copier
            </>
          )}
        </button>
      </div>

      {/* Contenu markdown rendu */}
      <div className="prose prose-sm max-w-none overflow-auto">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          rehypePlugins={[rehypeHighlight]}
          components={{
            // Personnalisation des composants
            h1: ({ children }) => (
              <h1 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b border-gray-200">
                {children}
              </h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-xl font-semibold text-gray-800 mb-3 mt-6">
                {children}
              </h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-lg font-medium text-gray-800 mb-2 mt-4">
                {children}
              </h3>
            ),
            table: ({ children }) => (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full divide-y divide-gray-200 border border-gray-300 rounded-lg">
                  {children}
                </table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="bg-gray-50">
                {children}
              </thead>
            ),
            th: ({ children }) => (
              <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-b border-gray-200">
                {children}
              </th>
            ),
            td: ({ children }) => (
              <td className="px-4 py-2 text-sm text-gray-900 border-b border-gray-100">
                {children}
              </td>
            ),
            code: ({ children, className }) => {
              const isInline = !className
              if (isInline) {
                return (
                  <code className="px-2 py-1 bg-gray-100 text-red-600 rounded text-sm font-mono">
                    {children}
                  </code>
                )
              }
              return (
                <code className={className}>
                  {children}
                </code>
              )
            },
            pre: ({ children }) => (
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4">
                {children}
              </pre>
            ),
            blockquote: ({ children }) => (
              <blockquote className="border-l-4 border-blue-500 pl-4 py-2 bg-blue-50 italic text-gray-700 my-4">
                {children}
              </blockquote>
            ),
            img: ({ src, alt }) => (
              <div className="my-4">
                <img 
                  src={src} 
                  alt={alt} 
                  className="max-w-full h-auto rounded-lg shadow-sm border border-gray-200" 
                />
                {alt && (
                  <p className="text-sm text-gray-600 text-center mt-2 italic">
                    {alt}
                  </p>
                )}
              </div>
            ),
            p: ({ children }) => (
              <p className="mb-4 text-gray-700 leading-relaxed">
                {children}
              </p>
            ),
            ul: ({ children }) => (
              <ul className="list-disc list-inside mb-4 space-y-1 text-gray-700">
                {children}
              </ul>
            ),
            ol: ({ children }) => (
              <ol className="list-decimal list-inside mb-4 space-y-1 text-gray-700">
                {children}
              </ol>
            ),
            li: ({ children }) => (
              <li className="ml-2">
                {children}
              </li>
            )
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  )
}

export default MarkdownPreview 