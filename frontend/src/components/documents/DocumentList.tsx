import { Button } from '@/components/ui/button'
import { deleteDocument } from '@/lib/api'
import type { Document } from '@/types'
import { useState } from 'react'

interface DocumentListProps {
  documents: Document[]
  loading: boolean
}

function StatusBadge({ status }: { status: Document['status'] }) {
  const styles = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function DocumentList({ documents, loading }: DocumentListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (doc: Document) => {
    if (!confirm(`Delete "${doc.filename}"? This cannot be undone.`)) return

    setDeletingId(doc.id)
    try {
      await deleteDocument(doc.id)
    } catch (error) {
      console.error('Failed to delete document:', error)
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading documents...</p>
  }

  if (documents.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-8">
        No documents uploaded yet. Upload a file to get started.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      {documents.map(doc => (
        <div
          key={doc.id}
          className="flex items-center justify-between p-3 rounded-lg border bg-card"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-medium truncate">{doc.filename}</p>
              <StatusBadge status={doc.status} />
            </div>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-muted-foreground">
                {formatFileSize(doc.file_size)}
              </span>
              {doc.status === 'completed' && (
                <span className="text-xs text-muted-foreground">
                  {doc.chunk_count} chunks
                </span>
              )}
              {doc.status === 'failed' && doc.error_message && (
                <span className="text-xs text-destructive truncate max-w-[200px]">
                  {doc.error_message}
                </span>
              )}
            </div>
            {doc.status === 'completed' && doc.metadata && (
              <div className="mt-2 space-y-1">
                <div className="flex flex-wrap gap-1.5">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                    {doc.metadata.document_type.replace(/_/g, ' ')}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    {doc.metadata.topic}
                  </span>
                  {doc.metadata.key_entities.slice(0, 3).map((entity) => (
                    <span
                      key={entity}
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
                    >
                      {entity}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {doc.metadata.summary}
                </p>
              </div>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDelete(doc)}
            disabled={deletingId === doc.id}
            className="text-muted-foreground hover:text-destructive"
          >
            {deletingId === doc.id ? '...' : 'Delete'}
          </Button>
        </div>
      ))}
    </div>
  )
}
