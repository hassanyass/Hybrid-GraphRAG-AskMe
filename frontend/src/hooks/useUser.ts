import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/api/client'
import { type User, useAuthStore } from '@/store/authStore'
import { supabase } from '@/lib/supabase'

export function useUserMe() {
  const setUser = useAuthStore((state) => state.setUser)
  const setLoading = useAuthStore((state) => state.setLoading)

  return useQuery({
    queryKey: ['users', 'me'],
    queryFn: async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        setUser(null)
        throw new Error('Not authenticated')
      }
      
      try {
        const { data } = await apiClient.get<User>('/users/me')
        setUser(data)
        return data
      } catch (error) {
        setUser(null)
        throw error
      } finally {
        setLoading(false)
      }
    },
    retry: false,
  })
}
