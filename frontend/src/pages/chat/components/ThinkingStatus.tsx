import { Check, Circle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ChatProgressState } from '@/services/ChatService'

interface ThinkingStatusProps {
  state: ChatProgressState
}

const states = [
  { id: 'understanding', label: 'Query understanding' },
  { id: 'searching', label: 'Searching documents' },
  { id: 'retrieving', label: 'Retrieving chunks' },
  { id: 'ranking', label: 'Context ranking' },
  { id: 'generating', label: 'Generating answer' },
]

export function ThinkingStatus({ state }: ThinkingStatusProps) {
  if (state === 'done') return null

  const currentIndex = states.findIndex(s => s.id === state)

  return (
    <div className="w-full max-w-sm rounded-lg border border-border bg-white shadow-sm p-4 font-sans mb-4">
      <div className="flex items-center gap-2 mb-3">
        <Loader2 className="w-4 h-4 text-accent animate-spin" />
        <span className="text-sm font-bold text-foreground">ASKME is thinking...</span>
      </div>
      <div className="flex flex-col gap-2 pl-1">
        {states.map((s, idx) => {
          const isCompleted = idx < currentIndex
          const isActive = idx === currentIndex
          const isPending = idx > currentIndex

          return (
            <div key={s.id} className="flex items-center gap-3">
              {isCompleted ? (
                <Check className="w-3.5 h-3.5 text-accent" />
              ) : isActive ? (
                <Circle className="w-3.5 h-3.5 text-accent fill-accent/20 animate-pulse" />
              ) : (
                <Circle className="w-3.5 h-3.5 text-neutral-300" />
              )}
              <span className={cn(
                "text-xs font-medium transition-colors",
                isCompleted ? "text-neutral-dark" : isActive ? "text-foreground" : "text-neutral-400"
              )}>
                {s.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
