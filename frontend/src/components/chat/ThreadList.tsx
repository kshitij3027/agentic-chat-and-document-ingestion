import { useState, useEffect, forwardRef, useImperativeHandle } from 'react'
import { MessageSquarePlus, Trash2, MessageSquare } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { listThreads, createThread, deleteThread } from '@/lib/api'
import type { Thread } from '@/types'
import { cn } from '@/lib/utils'

interface ThreadListProps {
  selectedThreadId: string | null
  onSelectThread: (threadId: string) => void
}

export interface ThreadListRef {
  updateThreadTitle: (threadId: string, title: string) => void
  addThread: (thread: Thread) => void
}

export const ThreadList = forwardRef<ThreadListRef, ThreadListProps>(
  function ThreadList({ selectedThreadId, onSelectThread }, ref) {
  const [threads, setThreads] = useState<Thread[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)

  useImperativeHandle(ref, () => ({
    updateThreadTitle: (threadId: string, title: string) => {
      setThreads(prev => prev.map(t =>
        t.id === threadId ? { ...t, title } : t
      ))
    },
    addThread: (thread: Thread) => {
      setThreads(prev => [thread, ...prev])
    }
  }))

  const loadThreads = async () => {
    try {
      const data = await listThreads()
      setThreads(data)
    } catch (error) {
      console.error('Failed to load threads:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadThreads()
  }, [])

  const handleCreateThread = async () => {
    setCreating(true)
    try {
      const newThread = await createThread()
      setThreads(prev => [newThread, ...prev])
      onSelectThread(newThread.id)
    } catch (error) {
      console.error('Failed to create thread:', error)
    } finally {
      setCreating(false)
    }
  }

  const handleDeleteThread = async (e: React.MouseEvent, threadId: string) => {
    e.stopPropagation()
    try {
      await deleteThread(threadId)
      setThreads(prev => prev.filter(t => t.id !== threadId))
      if (selectedThreadId === threadId) {
        onSelectThread('')
      }
    } catch (error) {
      console.error('Failed to delete thread:', error)
    }
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      <div className="p-4">
        <Button
          onClick={handleCreateThread}
          disabled={creating}
          className="w-full"
        >
          <MessageSquarePlus className="mr-2 h-4 w-4" />
          {creating ? 'Creating...' : 'New Chat'}
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-2">
        {threads.length === 0 ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No conversations yet. Start a new chat!
          </div>
        ) : (
          <div className="space-y-1">
            {threads.map(thread => (
              <div
                key={thread.id}
                onClick={() => onSelectThread(thread.id)}
                className={cn(
                  "group flex cursor-pointer items-center justify-between rounded-md px-3 py-2 text-sm hover:bg-accent",
                  selectedThreadId === thread.id && "bg-accent"
                )}
              >
                <div className="flex min-w-0 items-center gap-2">
                  <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                  <span className="truncate">{thread.title}</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100"
                  onClick={(e) => handleDeleteThread(e, thread.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
})
