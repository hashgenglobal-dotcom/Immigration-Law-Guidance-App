import Link from 'next/link'

export default function Header() {
  return (
    <header className="bg-primary-900 text-white shadow-lg">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold">
              Immigration Law Guidance
            </Link>
          </div>
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              <Link
                href="/"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
              >
                Home
              </Link>
              <Link
                href="/ask"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
              >
                Ask a Question
              </Link>
              <Link
                href="/scenarios"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
              >
                Scenarios
              </Link>
              <Link
                href="/about"
                className="px-3 py-2 rounded-md text-sm font-medium hover:bg-primary-700 transition-colors"
              >
                About
              </Link>
            </div>
          </div>
          <div className="md:hidden">
            {/* Mobile menu button - can be enhanced later */}
            <button className="text-white hover:bg-primary-700 px-3 py-2 rounded-md text-sm font-medium">
              Menu
            </button>
          </div>
        </div>
      </nav>
    </header>
  )
}
