import { Menu, LogOut, ChevronRight } from 'lucide-react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useUIStore } from '@/store/uiStore'
import { useAuthStore } from '@/store/authStore'
import { supabase } from '@/lib/supabase'

export function TopNavigation() {
  const { toggleSidebar } = useUIStore()
  const { setUser } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    setUser(null)
    navigate('/login')
  }

  // Very basic path formatting for the breadcrumb
  const path = location.pathname.split('/')[1] || 'dashboard'
  const formattedPath = path.charAt(0).toUpperCase() + path.slice(1)

  return (
    <header className="flex h-16 shrink-0 items-center border-b border-border bg-background px-4 md:px-6">
      <button
        onClick={toggleSidebar}
        className="mr-4 rounded p-1.5 text-neutral-dark hover:bg-neutral-light hover:text-foreground transition-colors"
      >
        <Menu className="h-5 w-5" />
      </button>
      
      <div className="flex items-center text-sm font-medium text-neutral-dark">
        <span className="text-foreground">My Knowledge Base</span>
        <ChevronRight className="mx-2 h-4 w-4 text-neutral-dark/50" />
        <span className="text-neutral-dark">{formattedPath === 'Dashboard' ? 'Home' : formattedPath}</span>
      </div>

      <div className="flex flex-1 items-center justify-end">
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 rounded px-3 py-1.5 text-sm text-neutral-dark hover:bg-neutral-light hover:text-foreground transition-colors"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Sign out</span>
        </button>
      </div>
    </header>
  )
}
