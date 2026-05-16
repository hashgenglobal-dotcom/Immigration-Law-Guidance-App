import { Button } from '@/components/ui/button'

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[50vh] max-w-lg flex-col items-center justify-center px-4 py-16 text-center">
      <p className="text-xs font-semibold uppercase tracking-widest text-sage-600">404</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight text-forest-900">Page not found</h1>
      <p className="mt-3 text-sage-800">
        The page you requested does not exist. Return home or ask a question about immigration law.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Button href="/" variant="primary" size="sm">
          Home
        </Button>
        <Button href="/ask" variant="secondary" size="sm">
          Ask a question
        </Button>
      </div>
    </div>
  )
}
