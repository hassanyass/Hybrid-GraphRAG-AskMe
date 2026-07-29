import { useNavigate } from 'react-router-dom'
import { LogOut } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useAuth } from '@/providers/AuthProvider'
import { supabase } from '@/lib/supabase'

interface UserProfileMenuProps {
  isCollapsed: boolean
}

export function UserProfileMenu({ isCollapsed }: UserProfileMenuProps) {
  const { user, setUser } = useAuthStore()
  const { session } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await supabase.auth.signOut()
    setUser(null)
    navigate('/login')
  }

  // If there is no backend user AND no Supabase session, do not render
  if (!user && !session) return null

  // Fallback to session email if backend user fetch failed
  const displayEmail = user?.email || session?.user.email || 'Unknown'
  const displayInitial = displayEmail.charAt(0).toUpperCase()
  const displayUsername = user?.username || 'User'

  return (
    <div className="flex items-center gap-3 rounded bg-white/5 p-3 border border-white/5">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-sm bg-secondary text-secondary-foreground font-semibold">
        {displayInitial}
      </div>
      
      {!isCollapsed && (
        <div className="flex flex-1 flex-col overflow-hidden">
          <span className="truncate text-sm font-medium text-white">
            {displayUsername}
          </span>
          <span className="truncate text-xs text-neutral-light/50">
            {displayEmail}
          </span>
        </div>
      )}

      {!isCollapsed && (
        <button
          onClick={handleLogout}
          className="rounded p-1.5 text-neutral-light/50 hover:bg-white/10 hover:text-white transition-colors"
          title="Sign Out"
        >
          <LogOut className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}
