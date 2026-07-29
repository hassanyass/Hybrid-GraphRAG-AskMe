import { PanelRightClose, PanelRightOpen, PanelLeftClose, PanelLeftOpen, Database, Link as LinkIcon, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

interface WorkspaceHeaderProps {
  workspaceName?: string
  documentCount?: number
  chunkCount?: number
  entityCount?: number
  lastUpdated?: string
  isLeftPaneOpen?: boolean
  toggleLeftPane?: () => void
  isRightPaneOpen: boolean
  toggleRightPane: () => void
}

export function WorkspaceHeader({
  workspaceName = 'Knowledge Workspace',
  documentCount = 0,
  chunkCount = 0,
  entityCount = 0,
  lastUpdated = 'Unknown',
  isLeftPaneOpen = true,
  toggleLeftPane,
  isRightPaneOpen,
  toggleRightPane
}: WorkspaceHeaderProps) {
  return (
    <div className="h-14 border-b border-border flex items-center justify-between px-4 lg:px-6 shrink-0 bg-white/95 backdrop-blur-sm z-20 shadow-sm">
      <div className="flex items-center gap-2 lg:gap-6 min-w-0 overflow-hidden">
        {toggleLeftPane && (
          <button
            onClick={toggleLeftPane}
            className={cn(
              "p-1.5 rounded-md transition-all flex items-center justify-center shrink-0",
              isLeftPaneOpen ? "bg-accent/10 text-accent" : "hover:bg-neutral-light text-neutral-dark"
            )}
            title="Toggle Left Drawer"
          >
            {isLeftPaneOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeftOpen className="w-4 h-4" />}
          </button>
        )}
         <h1 className="text-[15px] font-bold text-foreground tracking-tight truncate min-w-0">
           {workspaceName}
         </h1>
         <div className="hidden md:flex items-center gap-4 text-xs font-medium text-neutral-dark/80 shrink-0">
            <span className="flex items-center gap-1.5"><FileText className="w-3.5 h-3.5 text-accent" /> {documentCount} Documents</span>
            <span className="flex items-center gap-1.5"><Database className="w-3.5 h-3.5 text-accent" /> {chunkCount} Chunks</span>
            <span className="flex items-center gap-1.5"><LinkIcon className="w-3.5 h-3.5 text-accent" /> {entityCount} Entities</span>
         </div>
      </div>
      
      <div className="flex items-center gap-4">
        <span className="hidden lg:block text-xs text-neutral-dark/60 font-medium">Updated: {lastUpdated}</span>
        <button
          onClick={toggleRightPane}
          className={cn(
            "p-1.5 rounded-md transition-all flex items-center gap-2 text-xs font-bold uppercase tracking-wider",
            isRightPaneOpen ? "bg-accent/10 text-accent" : "hover:bg-neutral-light text-neutral-dark"
          )}
          title="Toggle Context Drawer"
        >
          {isRightPaneOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
          Context
        </button>
      </div>
    </div>
  )
}
