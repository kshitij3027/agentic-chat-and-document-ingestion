import { Search, Database, Globe, Loader2, Check } from 'lucide-react'
import type { ToolCallInfo } from '@/types'

const TOOL_ICONS: Record<string, typeof Search> = {
  search_documents: Search,
  query_sales_database: Database,
  web_search: Globe,
}

const TOOL_LABELS: Record<string, string> = {
  search_documents: 'Searching documents',
  query_sales_database: 'Querying database',
  web_search: 'Searching web',
}

interface ToolCallIndicatorProps {
  toolCall: ToolCallInfo
}

export function ToolCallIndicator({ toolCall }: ToolCallIndicatorProps) {
  const Icon = TOOL_ICONS[toolCall.tool_name] || Globe
  const label = TOOL_LABELS[toolCall.tool_name] || toolCall.tool_name
  const isRunning = toolCall.status === 'running'

  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span>{label}</span>
      {isRunning ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : (
        <>
          <Check className="h-3.5 w-3.5 text-green-500" />
          {toolCall.result_summary && (
            <span className="text-xs text-muted-foreground/70">({toolCall.result_summary})</span>
          )}
        </>
      )}
    </div>
  )
}
