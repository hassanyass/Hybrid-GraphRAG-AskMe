import { Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/providers/AuthProvider'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopNavigation } from '@/components/layout/TopNavigation'

export function ProtectedLayout() {
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
    // Use a microtask to avoid calling navigate during render
    queueMicrotask(() => navigate('/login', { replace: true }))
    return null
  }

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <TopNavigation />
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
