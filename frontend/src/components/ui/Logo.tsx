import { Network } from 'lucide-react'

interface LogoProps {
  className?: string
  collapsed?: boolean
}

export function Logo({ className = '', collapsed = false }: LogoProps) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* 
        Future graph-inspired identity placeholder.
        Currently uses a network icon to symbolize the knowledge graph,
        styled with the brand's primary Pearl Aqua and Dusty Grape accents.
      */}
      <div className="relative flex h-8 w-8 shrink-0 items-center justify-center rounded-sm bg-primary">
        <Network className="h-5 w-5 text-accent" />
      </div>
      {!collapsed && (
        <span className="text-xl font-bold tracking-tight">
          AskMe
        </span>
      )}
    </div>
  )
}
