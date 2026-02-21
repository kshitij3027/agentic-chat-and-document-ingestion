import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send } from 'lucide-react'
import { ThreadList, ThreadListRef } from '@/components/chat/ThreadList'
import { ChatView } from '@/components/chat/ChatView'
import { UserMenu } from '@/components/UserMenu'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/useAuth'
import { createThread } from '@/lib/api'
import logoSvg from '/logo.svg'

export function ChatPage() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [initialMessage, setInitialMessage] = useState<string | undefined>(undefined)
  const [welcomeInput, setWelcomeInput] = useState('')
  const [creating, setCreating] = useState(false)
  const { signOut, user, isAdmin } = useAuth()
  const threadListRef = useRef<ThreadListRef>(null)
  const navigate = useNavigate()

  const handleThreadTitleUpdate = (threadId: string, title: string) => {
    threadListRef.current?.updateThreadTitle(threadId, title)
  }

  const handleSelectThread = (threadId: string) => {
    setSelectedThreadId(threadId)
    setInitialMessage(undefined)
  }

  const handleWelcomeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!welcomeInput.trim() || creating) return

    const message = welcomeInput.trim()
    setCreating(true)
    try {
      const newThread = await createThread()
      threadListRef.current?.addThread(newThread)
      setInitialMessage(message)
      setSelectedThreadId(newThread.id)
      setWelcomeInput('')
    } catch (error) {
      console.error('Failed to create thread:', error)
    } finally {
      setCreating(false)
    }
  }

  const handleSignOut = async () => {
    try {
      await signOut()
    } catch (error) {
      console.error('Failed to sign out:', error)
    }
  }

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="flex w-64 flex-col border-r bg-muted/30">
        <div className="border-b p-4">
          <img src={logoSvg} alt="Logo" className="h-8" />
        </div>
        <nav className="border-b p-2">
          <div className="flex gap-1">
            <button className="flex-1 px-3 py-1.5 rounded-md text-sm bg-muted font-medium">
              Chat
            </button>
            <button
              onClick={() => navigate('/documents')}
              className="flex-1 px-3 py-1.5 rounded-md text-sm hover:bg-muted transition-colors"
            >
              Documents
            </button>
          </div>
        </nav>
        <ThreadList
          ref={threadListRef}
          selectedThreadId={selectedThreadId}
          onSelectThread={handleSelectThread}
        />
        <div className="border-t p-2">
          {user?.email && (
            <UserMenu email={user.email} onSignOut={handleSignOut} isAdmin={isAdmin} />
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1">
        {selectedThreadId ? (
          <ChatView
            threadId={selectedThreadId}
            onThreadTitleUpdate={handleThreadTitleUpdate}
            initialMessage={initialMessage}
          />
        ) : (
          <div className="flex h-full flex-col items-center justify-center">
            <h1 className="text-2xl font-medium mb-8">What can I help with?</h1>
            <form onSubmit={handleWelcomeSubmit} className="w-full max-w-2xl px-4">
              <div className="flex gap-2">
                <Input
                  value={welcomeInput}
                  onChange={(e) => setWelcomeInput(e.target.value)}
                  placeholder="Ask anything"
                  disabled={creating}
                  className="flex-1 rounded-full px-4"
                />
                <Button
                  type="submit"
                  size="icon"
                  className="rounded-full"
                  disabled={!welcomeInput.trim() || creating}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}
