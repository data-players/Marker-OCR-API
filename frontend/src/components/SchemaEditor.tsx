import React, { useState, useCallback } from 'react'
import { 
  Plus, 
  Trash2, 
  ChevronDown, 
  ChevronRight,
  HelpCircle,
  Copy,
  AlertCircle
} from 'lucide-react'

// Types with user-friendly labels
const FIELD_TYPES = {
  string: { label: 'Text' },
  number: { label: 'Number' },
  integer: { label: 'Integer' },
  boolean: { label: 'Boolean' },
  array: { label: 'Array' },
  object: { label: 'Object' },
} as const

type FieldType = keyof typeof FIELD_TYPES

// Root type is always 'object' - LLMs work better with object responses
// JSON technically allows arrays at root, but LLMs tend to wrap them in objects anyway
type RootType = 'object'

// Array item types
const ARRAY_ITEM_TYPES = ['string', 'number', 'integer', 'boolean', 'object'] as const

export interface SchemaField {
  id: string
  name: string
  type: FieldType
  description: string
  required: boolean
  itemType?: FieldType
  children?: SchemaField[]
}

export interface SchemaFieldDefinition {
  type: FieldType
  description: string
  required?: boolean
  items?: { type: string; properties?: Record<string, SchemaFieldDefinition> }
  properties?: Record<string, SchemaFieldDefinition>
}

export interface RootSchema {
  type: RootType
  itemType?: FieldType // For array root type
  fields: SchemaField[]
}

interface SchemaEditorProps {
  fields: SchemaField[]
  onChange: (fields: SchemaField[]) => void
  disabled?: boolean
}

// Generate unique ID
const generateId = () => `field_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

// Create a new empty field
const createEmptyField = (baseName: string = 'property'): SchemaField => ({
  id: generateId(),
  name: `${baseName}_${Date.now() % 1000}`,
  type: 'string',
  description: '',
  required: false,
})

// Property Editor Component
interface PropertyEditorProps {
  field: SchemaField
  onUpdate: (field: SchemaField) => void
  onDelete: () => void
  onDuplicate: () => void
  disabled?: boolean
  depth?: number
}

const PropertyEditor: React.FC<PropertyEditorProps> = ({
  field,
  onUpdate,
  onDelete,
  onDuplicate,
  disabled = false,
  depth = 0,
}) => {
  const [isExpanded, setIsExpanded] = useState(true) // Always expanded by default
  const [showDescription, setShowDescription] = useState(false) // Hidden by default
  
  const hasChildren = field.type === 'object' || (field.type === 'array' && field.itemType === 'object')
  const needsItemType = field.type === 'array'

  const handleNameChange = (name: string) => {
    const sanitized = name.replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase()
    onUpdate({ ...field, name: sanitized })
  }

  const handleTypeChange = (type: FieldType) => {
    const updatedField: SchemaField = { ...field, type }
    
    if (type === 'object') {
      updatedField.children = field.children || []
      delete updatedField.itemType
    } else if (type === 'array') {
      updatedField.itemType = field.itemType || 'string'
      if (updatedField.itemType === 'object') {
        updatedField.children = field.children || []
      } else {
        delete updatedField.children
      }
    } else {
      delete updatedField.children
      delete updatedField.itemType
    }
    
    onUpdate(updatedField)
  }

  const handleItemTypeChange = (itemType: FieldType) => {
    const updatedField: SchemaField = { ...field, itemType }
    
    if (itemType === 'object') {
      updatedField.children = field.children || []
    } else {
      delete updatedField.children
    }
    
    onUpdate(updatedField)
  }

  const handleAddChild = () => {
    const children = field.children || []
    onUpdate({
      ...field,
      children: [...children, createEmptyField()],
    })
  }

  const handleUpdateChild = (index: number, updatedChild: SchemaField) => {
    const children = [...(field.children || [])]
    children[index] = updatedChild
    onUpdate({ ...field, children })
  }

  const handleDeleteChild = (index: number) => {
    const children = (field.children || []).filter((_, i) => i !== index)
    onUpdate({ ...field, children })
  }

  const handleDuplicateChild = (index: number) => {
    const children = [...(field.children || [])]
    const duplicated = { ...children[index], id: generateId(), name: `${children[index].name}_copy` }
    children.splice(index + 1, 0, duplicated)
    onUpdate({ ...field, children })
  }

  return (
    <div className={`${depth > 0 ? 'ml-4 pl-3 border-l-2 border-white/10' : ''}`}>
      <div className={`
        bg-white/5 border rounded-lg overflow-hidden
        ${depth > 0 ? 'border-white/10' : 'border-white/20'}
        ${disabled ? 'opacity-60' : ''}
      `}>
        {/* Property Row */}
        <div className="flex items-center gap-2 p-2.5 bg-white/5">
          {/* Expand/Collapse */}
          {hasChildren ? (
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 hover:bg-white/10 rounded transition-colors"
              disabled={disabled}
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-gray-400" />
              ) : (
                <ChevronRight className="h-4 w-4 text-gray-400" />
              )}
            </button>
          ) : (
            <div className="w-6" />
          )}

          {/* Type Dropdown */}
          <select
            value={field.type}
            onChange={(e) => handleTypeChange(e.target.value as FieldType)}
            className="px-2 py-1 text-xs font-medium bg-slate-700 border border-white/20 rounded text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={disabled}
          >
            {Object.entries(FIELD_TYPES).map(([type, info]) => (
              <option key={type} value={type}>{info.label}</option>
            ))}
          </select>

          {/* Array Item Type */}
          {needsItemType && (
            <>
              <span className="text-xs text-gray-500">of</span>
              <select
                value={field.itemType || 'string'}
                onChange={(e) => handleItemTypeChange(e.target.value as FieldType)}
                className="px-2 py-1 text-xs font-medium bg-slate-700 border border-white/20 rounded text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                disabled={disabled}
              >
                {ARRAY_ITEM_TYPES.map((type) => (
                  <option key={type} value={type}>{FIELD_TYPES[type].label}</option>
                ))}
              </select>
            </>
          )}

          {/* Field Name */}
          <input
            type="text"
            value={field.name}
            onChange={(e) => handleNameChange(e.target.value)}
            className="flex-1 px-2 py-1 text-sm font-medium bg-slate-700 border border-white/20 rounded text-white placeholder-gray-500 focus:ring-2 focus:ring-purple-500 focus:border-transparent min-w-0"
            placeholder="property_name"
            disabled={disabled}
          />

          {/* Required Toggle */}
          <label className="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer select-none whitespace-nowrap">
            <input
              type="checkbox"
              checked={field.required}
              onChange={(e) => onUpdate({ ...field, required: e.target.checked })}
              className="rounded bg-slate-700 border-white/20 text-purple-500 focus:ring-purple-500 h-3.5 w-3.5"
              disabled={disabled}
            />
            Required
          </label>

          {/* Description Toggle */}
          <button
            type="button"
            onClick={() => setShowDescription(!showDescription)}
            className={`p-1.5 rounded transition-colors ${
              showDescription || field.description 
                ? 'text-purple-400 bg-purple-500/20' 
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/10'
            }`}
            title="Add description"
            disabled={disabled}
          >
            <HelpCircle className="h-3.5 w-3.5" />
          </button>

          {/* Duplicate */}
          <button
            type="button"
            onClick={onDuplicate}
            className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-white/10 rounded transition-colors"
            title="Duplicate"
            disabled={disabled}
          >
            <Copy className="h-3.5 w-3.5" />
          </button>

          {/* Delete */}
          <button
            type="button"
            onClick={onDelete}
            className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-500/20 rounded transition-colors"
            title="Delete"
            disabled={disabled}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Description Input */}
        {showDescription && (
          <div className="px-3 py-2 border-t border-white/10 bg-black/20">
            <input
              type="text"
              value={field.description}
              onChange={(e) => onUpdate({ ...field, description: e.target.value })}
              placeholder="Description (helps AI understand what to extract)..."
              className="w-full px-2 py-1.5 text-sm bg-slate-700 border border-white/20 rounded text-white placeholder-gray-500 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={disabled}
            />
          </div>
        )}

        {/* Nested Properties */}
        {hasChildren && isExpanded && (
          <div className="border-t border-white/10 bg-black/20 p-3">
            {field.children && field.children.length > 0 && (
              <div className="space-y-2 mb-3">
                {field.children.map((child, index) => (
                  <PropertyEditor
                    key={child.id}
                    field={child}
                    onUpdate={(updated) => handleUpdateChild(index, updated)}
                    onDelete={() => handleDeleteChild(index)}
                    onDuplicate={() => handleDuplicateChild(index)}
                    disabled={disabled}
                    depth={depth + 1}
                  />
                ))}
              </div>
            )}
            
            <button
              type="button"
              onClick={handleAddChild}
              className="w-full flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-purple-400 bg-purple-500/10 border border-dashed border-purple-500/30 rounded-lg hover:bg-purple-500/20 hover:border-purple-500/50 transition-colors"
              disabled={disabled}
            >
              <Plus className="h-3.5 w-3.5" />
              Add Property
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// Main Schema Editor Component with Root Block
// Root type is always 'object' - LLMs work best with object responses
const SchemaEditor: React.FC<SchemaEditorProps> = ({ 
  fields, 
  onChange, 
  disabled = false 
}) => {
  const [showJsonPreview, setShowJsonPreview] = useState(false)

  const handleAddField = useCallback(() => {
    onChange([...fields, createEmptyField()])
  }, [fields, onChange])

  const handleUpdateField = useCallback((index: number, updatedField: SchemaField) => {
    const newFields = [...fields]
    newFields[index] = updatedField
    onChange(newFields)
  }, [fields, onChange])

  const handleDeleteField = useCallback((index: number) => {
    onChange(fields.filter((_, i) => i !== index))
  }, [fields, onChange])

  const handleDuplicateField = useCallback((index: number) => {
    const newFields = [...fields]
    const duplicated = { ...fields[index], id: generateId(), name: `${fields[index].name}_copy` }
    newFields.splice(index + 1, 0, duplicated)
    onChange(newFields)
  }, [fields, onChange])

  const toJsonSchema = useCallback((fieldList: SchemaField[]): Record<string, SchemaFieldDefinition> => {
    const schema: Record<string, SchemaFieldDefinition> = {}
    
    for (const field of fieldList) {
      const definition: SchemaFieldDefinition = {
        type: field.type,
        description: field.description || `Extract ${field.name.replace(/_/g, ' ')}`,
        required: field.required,
      }

      if (field.type === 'object' && field.children) {
        definition.properties = toJsonSchema(field.children)
      }

      if (field.type === 'array' && field.itemType) {
        if (field.itemType === 'object' && field.children) {
          definition.items = {
            type: 'object',
            properties: toJsonSchema(field.children),
          }
        } else {
          definition.items = { type: field.itemType }
        }
      }

      schema[field.name] = definition
    }
    
    return schema
  }, [])

  const validationErrors = useCallback((): string[] => {
    const errors: string[] = []
    const names = new Set<string>()

    const validateField = (field: SchemaField, path: string = '') => {
      const fieldPath = path ? `${path}.${field.name}` : field.name
      
      if (!field.name.trim()) {
        errors.push(`Property at ${fieldPath || 'root'} must have a name`)
      } else if (names.has(fieldPath)) {
        errors.push(`Duplicate property name: ${fieldPath}`)
      } else {
        names.add(fieldPath)
      }

      if (field.type === 'object' && field.children) {
        for (const child of field.children) {
          validateField(child, fieldPath)
        }
      }

      if (field.type === 'array' && field.itemType === 'object' && field.children) {
        for (const child of field.children) {
          validateField(child, `${fieldPath}[]`)
        }
      }
    }

    for (const field of fields) {
      validateField(field)
    }

    return errors
  }, [fields])

  const errors = validationErrors()
  
  // Generate JSON schema - root is always object
  const jsonSchema = useCallback(() => {
    const propertiesSchema = toJsonSchema(fields)
    return {
      type: 'object',
      properties: propertiesSchema,
    }
  }, [fields, toJsonSchema])

  return (
    <div className="space-y-3">
      {/* Root Block - Always Object type */}
      <div className="border-2 border-purple-500/30 rounded-xl overflow-hidden bg-purple-500/5">
        {/* Root Header */}
        <div className="flex items-center gap-2 px-3 py-2.5 bg-purple-500/10 border-b border-purple-500/20">
          <span className="px-2 py-1 text-xs font-medium bg-slate-700 border border-purple-500/30 rounded text-purple-300">
            Object
          </span>
        </div>

        {/* Root Content - Properties */}
        <div className="p-3">
          {fields.length > 0 && (
            <div className="space-y-2 mb-3">
              {fields.map((field, index) => (
                <PropertyEditor
                  key={field.id}
                  field={field}
                  onUpdate={(updated) => handleUpdateField(index, updated)}
                  onDelete={() => handleDeleteField(index)}
                  onDuplicate={() => handleDuplicateField(index)}
                  disabled={disabled}
                  depth={0}
                />
              ))}
            </div>
          )}

          {/* Add Property Button */}
          <button
            type="button"
            onClick={handleAddField}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-purple-400 bg-purple-500/10 border-2 border-dashed border-purple-500/30 rounded-lg hover:bg-purple-500/20 hover:border-purple-500/50 transition-colors"
            disabled={disabled}
          >
            <Plus className="h-4 w-4" />
            Add Property
          </button>
        </div>
      </div>

      {/* Validation Errors */}
      {errors.length > 0 && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
          <div className="flex items-center gap-2 text-red-400 font-medium mb-2">
            <AlertCircle className="h-4 w-4" />
            Validation Issues
          </div>
          <ul className="text-sm text-red-300 list-disc list-inside space-y-1">
            {errors.map((error, i) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* JSON Preview */}
      {fields.length > 0 && (
        <div className="border-t border-white/10 pt-3">
          <button
            type="button"
            onClick={() => setShowJsonPreview(!showJsonPreview)}
            className="text-sm text-gray-400 hover:text-gray-300 flex items-center gap-1"
          >
            {showJsonPreview ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            {showJsonPreview ? 'Hide' : 'Show'} JSON Schema
          </button>
          
          {showJsonPreview && (
            <pre className="mt-2 p-3 bg-black/30 text-gray-300 rounded-lg text-xs overflow-auto max-h-48 border border-white/10">
              {JSON.stringify(jsonSchema(), null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  )
}

// Export utility functions - convert fields to properties schema
export const fieldsToSchema = (fields: SchemaField[]): Record<string, SchemaFieldDefinition> => {
  const schema: Record<string, SchemaFieldDefinition> = {}
  
  for (const field of fields) {
    const definition: SchemaFieldDefinition = {
      type: field.type,
      description: field.description || `Extract ${field.name.replace(/_/g, ' ')}`,
      required: field.required,
    }

    if (field.type === 'object' && field.children) {
      definition.properties = fieldsToSchema(field.children)
    }

    if (field.type === 'array' && field.itemType) {
      if (field.itemType === 'object' && field.children) {
        definition.items = {
          type: 'object',
          properties: fieldsToSchema(field.children),
        }
      } else {
        definition.items = { type: field.itemType }
      }
    }

    schema[field.name] = definition
  }
  
  return schema
}

// Export utility function - convert fields to full schema with root type
export interface RootSchemaOutput {
  type: 'object' | 'array'
  properties?: Record<string, SchemaFieldDefinition>
  items?: {
    type: string
    properties?: Record<string, SchemaFieldDefinition>
  }
}

// Convert fields to schema - root is always object
export const fieldsToSchemaWithRoot = (fields: SchemaField[]): RootSchemaOutput => {
  const propertiesSchema = fieldsToSchema(fields)
  return {
    type: 'object',
    properties: propertiesSchema,
  }
}

// Convert properties schema to fields (helper function)
const propertiesToFields = (properties: Record<string, any>): SchemaField[] => {
  const fields: SchemaField[] = []
  
  for (const [name, definition] of Object.entries(properties)) {
    if (!definition || typeof definition !== 'object') continue
    
    const field: SchemaField = {
      id: generateId(),
      name,
      type: (definition.type || 'string') as FieldType,
      description: definition.description || '',
      required: definition.required || false,
    }
    
    if (field.type === 'object' && definition.properties) {
      field.children = propertiesToFields(definition.properties)
    }
    
    if (field.type === 'array' && definition.items) {
      const itemType = definition.items.type || 'string'
      field.itemType = itemType as FieldType
      
      if (itemType === 'object' && definition.items.properties) {
        field.children = propertiesToFields(definition.items.properties)
      }
    }
    
    fields.push(field)
  }
  
  return fields
}

// Legacy: Convert old format schema (properties as root) to fields
export const schemaToFields = (schema: Record<string, any>): SchemaField[] => {
  return propertiesToFields(schema)
}

// Parse schema (supports both new and legacy formats) and extract fields
export const parseSchemaWithRoot = (schema: Record<string, any>): SchemaField[] => {
  // New format: { type: 'object', properties: {...} }
  if (schema.type === 'object' && schema.properties) {
    return propertiesToFields(schema.properties)
  }
  // Legacy format: { fieldName: { type, description, ... }, ... }
  return propertiesToFields(schema)
}

export const createInitialFields = (): SchemaField[] => []

export default SchemaEditor
