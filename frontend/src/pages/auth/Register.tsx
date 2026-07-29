import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/providers/AuthProvider'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

// Accept any email that ends with .com — no confirmation required
const registerSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .refine((val) => val.toLowerCase().endsWith('.com'), {
      message: 'Email must end with .com',
    }),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

type RegisterFormValues = z.infer<typeof registerSchema>

export function Register() {
  const navigate = useNavigate()
  const { session } = useAuth()
  const [error, setError] = useState<string | null>(null)

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  })

  // If already authenticated, redirect to dashboard
  if (session) {
    queueMicrotask(() => navigate('/projects', { replace: true }))
    return null
  }

  const onSubmit = async (data: RegisterFormValues) => {
    setError(null)

    try {
      // Call backend which uses the Supabase admin key to create + auto-confirm
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.email.trim().toLowerCase(), password: data.password }),
      })

      const json = await res.json()

      if (!res.ok) {
        setError(json.detail ?? 'Registration failed. Please try again.')
        return
      }

      // Restore the Supabase session from the tokens returned by the backend
      const { error: sessionError } = await supabase.auth.setSession({
        access_token: json.access_token,
        refresh_token: json.refresh_token,
      })

      if (sessionError) {
        setError(sessionError.message)
        return
      }

      navigate('/projects', { replace: true })
    } catch (err) {
      setError('Network error — please check your connection and try again.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md border-0 shadow-floating">
        <CardHeader className="space-y-2 text-center pb-8">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground font-bold text-xl">
            A
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight">Create workspace</CardTitle>
          <CardDescription>
            Enter your details to get started
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {error && (
              <div className="rounded-xl bg-red-50 p-3 text-sm text-red-500">
                {error}
              </div>
            )}
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="text"
                  placeholder="name@example.com"
                  {...register('email')}
                />
                {errors.email && <p className="text-sm text-red-500">{errors.email.message}</p>}
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  {...register('password')}
                />
                {errors.password && <p className="text-sm text-red-500">{errors.password.message}</p>}
              </div>
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Creating account...' : 'Create Account'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm text-neutral-dark">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-accent-hover hover:text-accent">
              Sign In
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
