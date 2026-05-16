'use client'

import Link from 'next/link'
import { BookOpen, Scale, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

const stripeClass =
  'h-[20rem] w-[10rem] bg-gradient-to-r from-cream-200/50 via-sage-300/40 to-sage-600/35 sm:h-[24rem] sm:w-[12rem]'

function GradientField() {
  return (
    <>
      <div className="pointer-events-none absolute right-[-30rem] top-[-40rem] z-0 flex skew-x-[-40deg] rotate-[-20deg] gap-[10rem] opacity-40 blur-[4rem]">
        <div className={stripeClass} />
        <div className={stripeClass} />
        <div className={stripeClass} />
      </div>
      <div className="pointer-events-none absolute right-[-50rem] top-[-50rem] z-0 flex skew-x-[-40deg] rotate-[-20deg] gap-[10rem] opacity-35 blur-[4rem]">
        <div className={stripeClass} />
        <div className={stripeClass} />
        <div className={stripeClass} />
      </div>
      <div className="pointer-events-none absolute right-[-60rem] top-[-60rem] z-0 flex skew-x-[-40deg] rotate-[-20deg] gap-[10rem] opacity-30 blur-[4rem]">
        <div className="h-[30rem] w-[10rem] bg-gradient-to-r from-cream-100/40 via-sage-400/35 to-forest-700/40 sm:w-[12rem]" />
        <div className="h-[30rem] w-[10rem] bg-gradient-to-r from-cream-100/40 via-sage-400/35 to-forest-700/40 sm:w-[12rem]" />
        <div className="h-[30rem] w-[10rem] bg-gradient-to-r from-cream-100/40 via-sage-400/35 to-forest-700/40 sm:w-[12rem]" />
      </div>
    </>
  )
}

const suggestions = [
  { label: 'Can I work while my asylum case is pending?', href: '/ask' },
  { label: 'I received a Notice to Appear', href: '/scenarios?s=nta' },
  { label: 'ICE came to my door', href: '/scenarios?s=ice-door' },
  { label: 'I want to apply for citizenship', href: '/scenarios?s=citizenship' },
  { label: 'What is advance parole?', href: '/ask' },
] as const

export function Hero1() {
  return (
    <section className="relative overflow-x-hidden border-b border-sage-600/30 bg-forest-900 text-cream-100">
      <GradientField />

      <div className="relative z-[1] mx-auto flex min-h-[min(88vh,52rem)] max-w-7xl flex-col px-4 pb-16 pt-12 sm:px-6 sm:pb-20 sm:pt-16 lg:px-8">
        <main className="flex flex-1 flex-col items-center justify-center px-2 text-center sm:px-4">
          <div className="mx-auto max-w-4xl space-y-6 sm:space-y-8">
            <div className="flex justify-center">
              <div className="mx-4 flex w-fit items-center gap-2 rounded-full border border-sage-400/45 bg-forest-800/90 px-4 py-2 backdrop-blur-sm">
                <span className="flex items-center gap-2 text-xs font-medium text-cream-200/95 sm:text-sm">
                  <span className="flex rounded-full bg-sage-500/90 p-1.5 text-cream-50 ring-1 ring-cream-200/20">
                    <Scale className="h-3.5 w-3.5 sm:h-4 sm:w-4" aria-hidden />
                  </span>
                  Official sources only — not answers from model memory
                </span>
              </div>
            </div>

            <h1 className="text-balance text-4xl font-bold leading-tight tracking-tight text-cream-50 sm:text-5xl lg:text-6xl">
              Immigration law information you can trace to real sources
            </h1>

            <p className="mx-auto max-w-2xl text-pretty text-base text-cream-200/95 sm:text-lg">
              A privacy-first assistant for plain-language guidance. Built so responses are grounded in retrieved USCIS,
              eCFR, and INA materials — with clear citations.
            </p>

            <div className="relative mx-auto mt-2 w-full max-w-2xl">
              <Link
                href="/ask"
                className="group flex items-center gap-1 rounded-full border border-sage-600/50 bg-forest-800/90 p-2 pl-3 shadow-lg shadow-black/20 backdrop-blur-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-sage-400/60 hover:bg-forest-800 hover:shadow-glow-gold"
              >
                <span className="rounded-full p-2 text-sage-300 transition group-hover:bg-forest-700/80 group-hover:text-cream-100">
                  <BookOpen className="h-5 w-5" aria-hidden />
                </span>
                <span className="rounded-full p-2 text-sage-300 transition group-hover:bg-forest-700/80 group-hover:text-cream-100">
                  <Sparkles className="h-5 w-5" aria-hidden />
                </span>
                <span className="flex-1 px-3 py-2 text-left text-sm text-cream-200/80 sm:text-base">
                  Ask your immigration question…
                </span>
                <span className="hidden rounded-full bg-sage-500 px-4 py-2 text-sm font-semibold text-cream-50 sm:inline-block">
                  Open assistant
                </span>
              </Link>
            </div>

            <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-sage-400/50 border-l-4 border-l-sage-500 bg-cream-200/98 px-4 py-3 text-center text-xs font-semibold uppercase leading-snug tracking-wide text-forest-900 shadow-card sm:text-sm">
              <span className="block">GENERAL LEGAL INFORMATION, NOT LEGAL ADVICE.</span>
              <span className="mt-1.5 block">HIGH-RISK SITUATIONS - TAKE A LEGAL ADVICE FROM ATTORNEY</span>
            </div>

            <div className="flex flex-col items-stretch justify-center gap-3 pt-2 sm:flex-row sm:justify-center">
              <Button href="/ask" variant="primary" size="lg" className="btn-pill">
                Ask a question
              </Button>
              <Button href="/scenarios" variant="outline-dark" size="lg" className="btn-pill">
                Browse scenarios
              </Button>
            </div>

            <div className="mx-auto flex max-w-2xl flex-wrap justify-center gap-2 pt-4">
              {suggestions.map((item) => (
                <Link
                  key={item.label}
                  href={item.href}
                  className="pill-dark text-left"
                >
                  {item.label}
                </Link>
              ))}
            </div>

            <p className="pt-2 text-xs font-semibold uppercase tracking-[0.2em] text-sage-300/90">HashGen Global LLC · MVP</p>
          </div>
        </main>
      </div>
    </section>
  )
}
