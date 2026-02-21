import { useEffect, useState, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import { listDocuments } from '@/lib/api'
import type { Document } from '@/types'

export function useRealtimeDocuments(userId: string | undefined) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  const fetchDocuments = useCallback(async () => {
    if (!userId) return
    try {
      const docs = await listDocuments()
      setDocuments(docs)
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  useEffect(() => {
    if (!userId) return

    const channel = supabase
      .channel('documents-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'documents',
          filter: `user_id=eq.${userId}`,
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setDocuments(prev => [payload.new as Document, ...prev])
          } else if (payload.eventType === 'UPDATE') {
            setDocuments(prev =>
              prev.map(doc =>
                doc.id === (payload.new as Document).id
                  ? (payload.new as Document)
                  : doc
              )
            )
          } else if (payload.eventType === 'DELETE') {
            setDocuments(prev =>
              prev.filter(doc => doc.id !== (payload.old as { id: string }).id)
            )
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [userId])

  return { documents, loading, refetch: fetchDocuments }
}
