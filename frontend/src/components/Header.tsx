'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

const nav = [
  { href: '/', label: 'Home' },
  { href: '/ask', label: 'Ask a Question' },
  { href: '/scenarios', label: 'Scenarios' },
  { href: '/about', label: 'About' },
] as const

function LogoMark() {
  return (
    <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden className="shrink-0 text-cream-200/90">
      <defs>
        <linearGradient id="logoGrad" x1="6" y1="4" x2="26" y2="28" gradientUnits="userSpaceOnUse">
          <stop stopColor="#567470" />
          <stop offset="1" stopColor="#0C2924" />
        </linearGradient>
      </defs>
      <rect x="3" y="6" width="26" height="20" rx="5" fill="url(#logoGrad)" opacity="0.95" />
      <path
        d="M11 22V12l5 4 5-4v10"
        fill="none"
        stroke="#F3EEED"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default function Header() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    setOpen(false)
  }, [pathname])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  return (
    <header className="sticky top-0 z-40 border-b border-sage-800/40 bg-forest-900/95 text-cream-200 shadow-sm backdrop-blur">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="flex items-center gap-3 rounded-md outline-none ring-offset-2 ring-offset-forest-900 focus-visible:ring-2 focus-visible:ring-cream-200/80"
        >
          <LogoMark />
          <span className="text-base font-semibold tracking-tight text-cream-50 sm:text-lg">Immigration Law Guidance</span>
        </Link>

        <div className="hidden items-center gap-1 md:flex">
          {nav.map((item) => {
            const active = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  active ? 'bg-sage-500 text-cream-50' : 'text-cream-200/90 hover:bg-forest-800/80 hover:text-cream-50'
                }`}
              >
                {item.label}
              </Link>
            )
          })}
        </div>

        <button
          type="button"
          className="inline-flex items-center justify-center rounded-lg px-3 py-2 text-sm font-semibold text-cream-200 outline-none ring-offset-2 ring-offset-forest-900 hover:bg-forest-800/80 focus-visible:ring-2 focus-visible:ring-cream-200/80 md:hidden"
          aria-expanded={open}
          aria-controls="mobile-nav"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? 'Close' : 'Menu'}
        </button>
      </nav>

      {open ? (
        <div id="mobile-nav" className="border-t border-sage-800/40 bg-forest-900 md:hidden">
          <div className="mx-auto max-w-7xl space-y-1 px-4 py-3 sm:px-6">
            {nav.map((item) => {
              const active = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block rounded-lg px-3 py-2 text-sm font-medium ${
                    active ? 'bg-sage-500 text-cream-50' : 'text-cream-200/90 hover:bg-forest-800/80'
                  }`}
                >
                  {item.label}
                </Link>
              )
            })}
          </div>
        </div>
      ) : null}
    </header>
  )
}
