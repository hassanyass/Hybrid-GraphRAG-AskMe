import type { Source } from '@/hooks/useChat'
import { FileText, ArrowRight } from 'lucide-react'

interface SourcesPaneProps {
  sources?: Source[]
  onSourceClick?: (source: Source) => void
}

export function SourcesPane({ sources, onSourceClick }: SourcesPaneProps) {
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
          <div 
            key={idx} 
            className="rounded border border-border bg-white transition-all hover:border-accent hover:shadow-sm cursor-pointer group"
            onClick={() => onSourceClick?.(source)}
          >
            <div className="p-4 space-y-3">
              <div className="flex items-start justify-between gap-2 border-b border-border/50 pb-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-5 min-w-[20px] items-center justify-center rounded-sm bg-accent text-[10px] font-bold text-primary">
                    {idx + 1}
                  </div>
                  <span className="text-sm font-semibold text-foreground truncate max-w-[200px]" title={source.filename || 'Unknown Document'}>
                    📄 {source.filename || "Unknown Document"}
                  </span>
                </div>
              </div>
              
              {(source.page_number || source.section_title) && (
                <div className="flex flex-wrap gap-2 text-xs font-medium text-neutral-dark">
                  {source.page_number && <span>Page {source.page_number}</span>}
                  {source.page_number && source.section_title && <span>•</span>}
                  {source.section_title && <span>{source.section_title}</span>}
                </div>
              )}

              <p className="text-sm text-neutral-dark leading-relaxed line-clamp-3">
                "{source.preview || source.content || source.text || ""}"
              </p>
              
              <div className="flex justify-between items-center pt-2 border-t border-border/50 mt-2">
                <span className="text-xs font-semibold text-accent flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  Open Source <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
