import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { Session } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { useAuthStore } from '@/store/authStore'

interface AuthContextType {
  session: Session | null
  isReady: boolean
}

const AuthContext = createContext<AuthContextType>({ session: null, isReady: false })

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [isReady, setIsReady] = useState(false)
  const { setUser, setLoading } = useAuthStore()

  useEffect(() => {
    // 1. Check for existing session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      if (!session) {
        setUser(null)
      }
      setIsReady(true)
      setLoading(false)
    })

    // 2. Listen for ALL auth state changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session)
        if (!session) {
          setUser(null)
        }
      }
    )

    return () => subscription.unsubscribe()
  }, [setUser, setLoading])

  return (
    <AuthContext.Provider value={{ session, isReady }}>
      {children}
    </AuthContext.Provider>
  )
}
