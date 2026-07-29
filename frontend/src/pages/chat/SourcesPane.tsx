import type { Source } from '@/hooks/useChat'
import { FileText, ChevronRight } from 'lucide-react'

interface SourcesPaneProps {
  sources?: Source[]
}

export function SourcesPane({ sources }: SourcesPaneProps) {
  if (!sources || sources.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center text-neutral-dark">
        <FileText className="mb-4 h-12 w-12 opacity-20" />
        <p className="text-sm font-medium text-foreground">No sources active</p>
        <p className="mt-1 text-xs">Converse with the knowledge base to view retrieved evidence.</p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col overflow-hidden p-6 animate-in fade-in slide-in-from-right-4 duration-300">
      <h3 className="shrink-0 font-semibold text-lg flex items-center gap-2 text-foreground mb-6">
        <FileText className="h-5 w-5 text-accent" />
        Evidence
      </h3>
      
      <div className="flex-1 space-y-4 overflow-y-auto pr-2 no-scrollbar">
        {sources.map((source, idx) => (
          <div key={idx} className="rounded border border-border bg-white transition-colors hover:border-accent">
            <div className="p-4 space-y-3">
              <div className="flex items-start justify-between gap-2 border-b border-border/50 pb-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-5 min-w-[20px] items-center justify-center rounded-sm bg-neutral-light text-[10px] font-bold text-neutral-dark">
                    {idx + 1}
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-neutral-dark truncate max-w-[150px]" title={source.document_id || 'Unknown'}>
                    Doc: {source.document_id?.split('-')[0] || "Unknown"}
                  </span>
                </div>
                <div className="rounded-sm bg-accent/10 px-1.5 py-0.5 text-[10px] font-bold text-accent">
                  {((source.score || 0) * 100).toFixed(1)}% Match
                </div>
              </div>
              
              <p className="text-sm text-foreground leading-relaxed line-clamp-4">
                "{source.content || source.text || ""}"
              </p>
              
              {source.page_number && (
                <div className="flex justify-end pt-2">
                  <span className="text-xs font-medium text-neutral-dark flex items-center gap-1">
                    Page {source.page_number} <ChevronRight className="h-3 w-3" />
                  </span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
