import { Link, useLocation } from 'react-router-dom'
import { Settings, Database, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useUIStore } from '@/store/uiStore'
import { useWorkspaces } from '@/hooks/useWorkspaces'
import { UserProfileMenu } from './UserProfileMenu'
import { Logo } from '../ui/Logo'


export function Sidebar() {
  const location = useLocation()
  const { isSidebarOpen } = useUIStore()
  const { data: workspaces } = useWorkspaces()

  return (
    <aside
      className={cn(
        "flex flex-col h-full bg-primary text-primary-foreground transition-all duration-300 ease-in-out border-r border-neutral-dark/20",
        isSidebarOpen ? "w-64" : "w-20"
      )}
    >
      <div className="flex h-16 shrink-0 items-center px-5 border-b border-white/5">
        <Logo collapsed={!isSidebarOpen} />
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        {/* Current Knowledge Space Context */}
        <div className="px-4 mb-6">
          {isSidebarOpen && (
            <div className="mb-2 text-xs font-semibold tracking-wider text-neutral-light/50 uppercase">
              Current Space
            </div>
          )}
          <button className={cn(
            "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium bg-white/5 hover:bg-white/10 transition-colors border border-white/10",
            !isSidebarOpen && "justify-center px-0"
          )}>
            <Database className="h-4 w-4 text-accent shrink-0" />
            {isSidebarOpen && <span className="truncate">My Knowledge Base</span>}
          </button>
        </div>

        {/* Primary Navigation within the Space */}
        <nav className="space-y-1 px-4 mb-8">
          <Link
            to="/projects"
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              location.pathname === '/projects' 
                ? "bg-accent/10 text-accent" 
                : "text-neutral-light/70 hover:bg-white/5 hover:text-white",
              !isSidebarOpen && "justify-center px-0"
            )}
          >
            <Database className="h-4 w-4 shrink-0" />
            {isSidebarOpen && <span>Projects</span>}
          </Link>
        </nav>

        {/* Recent Spaces */}
        {isSidebarOpen && workspaces && workspaces.length > 0 && (
          <div className="px-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold tracking-wider text-neutral-light/50 uppercase">
                Recent Spaces
              </span>
              <Link to="/projects" className="text-neutral-light/50 hover:text-white transition-colors">
                <Plus className="h-4 w-4" />
              </Link>
            </div>
            <div className="space-y-1">
              {workspaces.slice(0, 2).map((workspace) => (
                <Link
                  key={workspace.id}
                  to={`/projects/${workspace.id}/chat`}
                  className="block w-full text-left truncate rounded-lg px-3 py-1.5 text-xs text-neutral-light/70 hover:bg-white/5 hover:text-white transition-colors"
                >
                  {workspace.name}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-white/5">
        <div className="space-y-1 mb-4">
          <Link
            to="/settings"
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-neutral-light/70 hover:bg-white/5 hover:text-white transition-colors",
              !isSidebarOpen && "justify-center px-0"
            )}
          >
            <Settings className="h-4 w-4 shrink-0" />
            {isSidebarOpen && <span>Settings</span>}
          </Link>
        </div>
        <UserProfileMenu isCollapsed={!isSidebarOpen} />
      </div>
    </aside>
  )
}
