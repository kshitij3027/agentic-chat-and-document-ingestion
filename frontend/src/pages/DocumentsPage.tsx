import { useAuth } from '@/hooks/useAuth'
import { useRealtimeDocuments } from '@/hooks/useRealtimeDocuments'
import { DocumentUpload } from '@/components/documents/DocumentUpload'
import { DocumentList } from '@/components/documents/DocumentList'
import { UserMenu } from '@/components/UserMenu'
import { useNavigate } from 'react-router-dom'

export function DocumentsPage() {
  const { user, signOut, isAdmin } = useAuth()
  const { documents, loading, refetch } = useRealtimeDocuments(user?.id)
  const navigate = useNavigate()

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
          <h1 className="text-lg font-semibold tracking-tight">Agentic Chat & Ingestion</h1>
        </div>
        <nav className="border-b p-2">
          <div className="flex gap-1">
            <button
              onClick={() => navigate('/')}
              className="flex-1 px-3 py-1.5 rounded-md text-sm hover:bg-muted transition-colors"
            >
              Chat
            </button>
            <button className="flex-1 px-3 py-1.5 rounded-md text-sm bg-muted font-medium">
              Documents
            </button>
          </div>
        </nav>
        <div className="flex-1" />
        <div className="border-t p-2">
          {user?.email && (
            <UserMenu email={user.email} onSignOut={handleSignOut} isAdmin={isAdmin} />
          )}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-3xl mx-auto p-8 space-y-8">
          <div>
            <h1 className="text-2xl font-bold">Documents</h1>
            <p className="text-muted-foreground mt-1">
              Upload documents to use as context in your chats.
            </p>
          </div>

          <DocumentUpload onUploadComplete={refetch} />
          <DocumentList documents={documents} loading={loading} />
        </div>
      </div>
    </div>
  )
}
