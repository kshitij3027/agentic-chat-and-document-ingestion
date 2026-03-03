import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { ToolCallIndicator } from './ToolCallIndicator'
import type { ToolCallInfo } from '@/types'

interface StepsPanelProps {
  toolCalls: ToolCallInfo[]
}

function getQueryFromArgs(args: string): string {
  try {
    const parsed = JSON.parse(args)
    return parsed.query || parsed.sql || ''
  } catch {
    return ''
  }
}

export function StepsPanel({ toolCalls }: StepsPanelProps) {
  const [expanded, setExpanded] = useState(false)

  if (!toolCalls || toolCalls.length === 0) return null

  const allCompleted = toolCalls.every(tc => tc.status === 'completed')
  const header = allCompleted
    ? `Used ${toolCalls.length} tool${toolCalls.length > 1 ? 's' : ''}`
    : `Running ${toolCalls.length} tool${toolCalls.length > 1 ? 's' : ''}...`

  return (
    <div className="mb-2 rounded-lg border bg-muted/30 px-3 py-2 text-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5" />
        )}
        <span className="font-medium">{header}</span>
      </button>

      {expanded && (
        <div className="mt-2 space-y-1.5 pl-5">
          {toolCalls.map((tc, i) => (
            <div key={i}>
              <ToolCallIndicator toolCall={tc} />
              {getQueryFromArgs(tc.arguments) && (
                <p className="pl-5.5 text-xs text-muted-foreground/60 truncate max-w-md">
                  {getQueryFromArgs(tc.arguments)}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
