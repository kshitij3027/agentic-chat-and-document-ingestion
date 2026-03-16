import { useState } from 'react'
import { ChevronDown, ChevronRight, FileSearch, Loader2, Check, AlertCircle } from 'lucide-react'
import type { SubAgentState } from '@/types'

function stripThinkTags(text: string): string {
  let result = text.replace(/<think>[\s\S]*?<\/think>\s*/gi, '')
  result = result.replace(/<think>[\s\S]*$/gi, '')
  return result.trim()
}

interface SubAgentPanelProps {
  subAgent: SubAgentState
}

export function SubAgentPanel({ subAgent }: SubAgentPanelProps) {
  const [expanded, setExpanded] = useState(true)

  const statusIcon = {
    running: <Loader2 className="h-4 w-4 animate-spin text-blue-500" />,
    completed: <Check className="h-4 w-4 text-green-500" />,
    error: <AlertCircle className="h-4 w-4 text-red-500" />,
  }[subAgent.status]

  const cleanedReasoning = stripThinkTags(subAgent.reasoning || '')

  return (
    <div className="mb-2 rounded-lg border bg-muted/30 overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0" />
        )}
        <FileSearch className="h-4 w-4 shrink-0" />
        <span className="font-medium">
          Analyzing: {subAgent.filename || 'document'}
        </span>
        <span className="ml-auto">{statusIcon}</span>
      </button>

      {expanded && cleanedReasoning && (
        <div className="px-3 pb-3">
          <div className="rounded bg-background p-3 max-h-64 overflow-y-auto">
            <pre className="text-xs font-mono whitespace-pre-wrap text-muted-foreground">
              {cleanedReasoning}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
