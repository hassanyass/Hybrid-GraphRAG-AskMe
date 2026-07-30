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
import { Logo } from '@/components/ui/Logo'

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
    <div className="flex min-h-screen">
      {/* Left side branding / image */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-neutral-900 overflow-hidden group">
        <img 
          src="/auth-bg.png" 
          alt="AI Knowledge Graph Background" 
          className="absolute inset-0 w-full h-full object-cover opacity-90 transition-transform duration-[20s] ease-in-out group-hover:scale-110"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent flex flex-col justify-end p-12">
          
          <div className="relative z-10 backdrop-blur-xl bg-black/70 p-8 rounded-3xl border border-white/10 shadow-2xl transform transition-all duration-700 translate-y-0 opacity-100">
            <div className="flex items-center gap-3 mb-8">
              <Logo collapsed={false} className="text-white drop-shadow-lg" />
            </div>
            
            <h2 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-br from-white via-white to-white/50 mb-6 leading-tight tracking-tight drop-shadow-sm">
              Intelligent Document Analysis
            </h2>
            
            <p className="text-lg text-neutral-200 max-w-lg leading-relaxed font-medium">
              Interact with your documents, discover hidden insights, and construct powerful knowledge graphs effortlessly.
            </p>
          </div>
          
        </div>
      </div>

      {/* Right side form */}
      <div className="flex w-full lg:w-1/2 items-center justify-center bg-background px-4 py-12">
        <Card className="w-full max-w-md border-0 shadow-none">
          <CardHeader className="space-y-2 text-center pb-8">
            <div className="flex justify-center mb-4 lg:hidden">
              <Logo collapsed={false} />
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight">Create Project</CardTitle>
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
    </div>
  )
}
