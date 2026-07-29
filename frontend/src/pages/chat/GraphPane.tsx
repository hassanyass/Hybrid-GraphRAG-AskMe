import type { Entity } from '@/hooks/useChat'
import { Network } from 'lucide-react'

interface GraphPaneProps {
  entities?: Entity[]
}

export function GraphPane({ entities }: GraphPaneProps) {
  if (!entities || entities.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center p-8 text-center text-neutral-dark">
        <Network className="mb-4 h-12 w-12 opacity-20" />
        <p className="text-sm font-medium text-foreground">No entities extracted</p>
        <p className="mt-1 text-xs">Knowledge graph relationships will appear here.</p>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col overflow-hidden p-6 animate-in fade-in slide-in-from-right-4 duration-300">
      <h3 className="shrink-0 font-semibold text-lg flex items-center gap-2 text-foreground mb-6">
        <Network className="h-5 w-5 text-accent" />
        Knowledge Nodes
      </h3>
      
      <div className="flex-1 overflow-y-auto flex flex-wrap gap-2 no-scrollbar pr-2">
        {entities.map((entity, idx) => (
          <div key={idx} className="p-3 bg-white border border-border rounded-lg shadow-sm">
            <div className="font-semibold text-foreground">{entity.id}</div>
            <div className="text-xs text-neutral-dark mt-1 flex gap-2">
              <span className="bg-accent/10 text-accent px-1.5 py-0.5 rounded uppercase font-bold tracking-wider">{entity.label || 'Entity'}</span>
            </div>
            {entity.properties && (
              <div className="mt-2 pt-2 border-t border-border/50 text-[10px] text-neutral-dark grid grid-cols-2 gap-x-2 gap-y-1">
                {Object.entries(entity.properties).map(([key, value]) => (
                  <div key={key}>
                    <span className="font-medium opacity-70">{key}:</span> {String(value)}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
