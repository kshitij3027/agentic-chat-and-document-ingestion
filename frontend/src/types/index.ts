export interface Thread {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  thread_id: string
  user_id: string
  openai_message_id: string | null
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface Document {
  id: string
  user_id: string
  filename: string
  file_type: string
  file_size: number
  storage_path: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message: string | null
  chunk_count: number
  created_at: string
  updated_at: string
}
