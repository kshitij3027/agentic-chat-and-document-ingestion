import { useState, useEffect, useRef } from 'react'
import { Send, Square, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getMessages, sendMessage, updateThread } from '@/lib/api'
import type { Message } from '@/types'

interface ChatViewProps {
  threadId: string
  onThreadTitleUpdate?: (threadId: string, title: string) => void
  initialMessage?: string
}

export function ChatView({ threadId, onThreadTitleUpdate, initialMessage }: ChatViewProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [waiting, setWaiting] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const initialMessageSentRef = useRef(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent])

  useEffect(() => {
    let cancelled = false
    initialMessageSentRef.current = false

    const loadMessages = async () => {
      setLoading(true)
      try {
        const data = await getMessages(threadId)
        if (!cancelled) {
          setMessages(data)
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load messages:', error)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadMessages()
    return () => { cancelled = true }
  }, [threadId])

  const doSend = async (userMessage: string) => {
    if (!userMessage.trim() || sending) return

    const isFirstMessage = messages.length === 0
    setSending(true)
    setWaiting(true)
    setStreamingContent('')
    setError(null)

    abortControllerRef.current = new AbortController()

    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      thread_id: threadId,
      user_id: '',
      openai_message_id: null,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMessage])

    if (isFirstMessage && onThreadTitleUpdate) {
      const title = userMessage.length > 50
        ? userMessage.substring(0, 47) + '...'
        : userMessage
      try {
        await updateThread(threadId, title)
        onThreadTitleUpdate(threadId, title)
      } catch (error) {
        console.error('Failed to update thread title:', error)
      }
    }

    try {
      await sendMessage({
        threadId,
        content: userMessage,
        onTextDelta: (text) => {
          setWaiting(false)
          setStreamingContent(prev => prev + text)
        },
        onDone: () => {
          setSending(false)
          setWaiting(false)
          abortControllerRef.current = null
        },
        onError: (err) => {
          console.error('Stream error:', err)
          setError(err)
          setSending(false)
          setWaiting(false)
          abortControllerRef.current = null
        },
        signal: abortControllerRef.current.signal,
      })
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        setSending(false)
        setWaiting(false)
      } else {
        console.error('Failed to send message:', err)
        setError((err as Error).message || 'Failed to send message')
        setSending(false)
        setWaiting(false)
      }
      abortControllerRef.current = null
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sending) return
    const userMessage = input.trim()
    setInput('')
    await doSend(userMessage)
  }

  useEffect(() => {
    if (!loading && initialMessage && !initialMessageSentRef.current) {
      initialMessageSentRef.current = true
      doSend(initialMessage)
    }
  }, [loading, initialMessage])

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
  }

  useEffect(() => {
    if (!sending && streamingContent) {
      setMessages(prev => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          thread_id: threadId,
          user_id: '',
          openai_message_id: null,
          role: 'assistant',
          content: streamingContent,
          created_at: new Date().toISOString(),
        } as Message,
      ])
      setStreamingContent('')
    }
  }, [sending, streamingContent, threadId])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 && !streamingContent && !waiting && !error ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center text-muted-foreground">
              <p className="text-2xl font-medium mb-2">What can I help with?</p>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl px-4 py-8">
            <div className="space-y-6">
              {messages.map(message => (
                <div key={message.id}>
                  {message.role === 'user' ? (
                    <div className="flex justify-end">
                      <div className="max-w-[85%] rounded-3xl bg-secondary px-5 py-3">
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      </div>
                    </div>
                  ) : (
                    <div className="prose prose-neutral dark:prose-invert max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>
              ))}

              {/* Loading indicator */}
              {waiting && !streamingContent && (
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm">Thinking...</span>
                </div>
              )}

              {/* Streaming message */}
              {streamingContent && (
                <div className="prose prose-neutral dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {streamingContent}
                  </ReactMarkdown>
                </div>
              )}

              {/* Error message */}
              {error && (
                <div className="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t bg-background">
        <div className="mx-auto max-w-3xl px-4 py-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything"
              disabled={sending}
              className="flex-1 rounded-full px-4"
            />
            {sending ? (
              <Button
                type="button"
                variant="destructive"
                size="icon"
                className="rounded-full"
                onClick={handleStop}
                title="Stop generating"
              >
                <Square className="h-4 w-4" />
              </Button>
            ) : (
              <Button
                type="submit"
                size="icon"
                className="rounded-full"
                disabled={!input.trim()}
              >
                <Send className="h-4 w-4" />
              </Button>
            )}
          </form>
        </div>
      </div>
    </div>
  )
}
