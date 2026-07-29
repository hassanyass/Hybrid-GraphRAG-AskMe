import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 text-center">
      <div className="mb-8 flex h-20 w-20 items-center justify-center rounded-3xl bg-neutral-light text-4xl font-bold text-neutral-dark">
        404
      </div>
      <h1 className="mb-2 text-3xl font-bold tracking-tight">Page not found</h1>
      <p className="mb-8 text-neutral-dark">
        The page you are looking for doesn't exist or has been moved.
      </p>
      <Button asChild>
        <Link to="/">Return Home</Link>
      </Button>
    </div>
  )
}
