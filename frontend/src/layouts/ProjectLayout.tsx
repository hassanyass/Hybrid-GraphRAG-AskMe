import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/providers/AuthProvider'

export function ProjectLayout() {
  const navigate = useNavigate()
  const { session, isReady } = useAuth()

  // Show spinner while the initial session check is resolving
  if (!isReady) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-neutral-light border-t-accent"></div>
      </div>
    )
  }

  // No session after initial check → redirect to login
  if (!session) {
    queueMicrotask(() => navigate('/login', { replace: true }))
    return null
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* 
        This is an isolated layout specifically for an active Knowledge Space (Project).
        It does NOT include the global Sidebar or TopNavigation.
      */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}
