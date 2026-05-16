'use client'

import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import PageHeader from '@/components/PageHeader'
import { RiskBadge } from '@/components/RiskBadge'

interface Scenario {
  id: string
  title: string
  riskLevel: 'low' | 'medium' | 'high'
  description: string
  shortDescription: string
}

const scenarios: Scenario[] = [
  {
    id: 'ice-door',
    title: 'ICE came to my door',
    riskLevel: 'high',
    description: 'Immigration officers are at your residence',
    shortDescription: 'Know your rights when ICE agents arrive',
  },
  {
    id: 'overstay',
    title: 'I overstayed my visa',
    riskLevel: 'medium',
    description: 'Your visa has expired and you are out of status',
    shortDescription: 'Understanding options after visa expiration',
  },
  {
    id: 'nta',
    title: 'I received a Notice to Appear',
    riskLevel: 'high',
    description: 'You have been placed in removal proceedings',
    shortDescription: 'What to do after receiving an NTA',
  },
  {
    id: 'asylum',
    title: 'I want to apply for asylum',
    riskLevel: 'medium',
    description: 'Seeking protection due to persecution in home country',
    shortDescription: 'Asylum application process and requirements',
  },
  {
    id: 'citizenship',
    title: 'I want to apply for citizenship',
    riskLevel: 'low',
    description: 'Naturalization process for permanent residents',
    shortDescription: 'N-400 application requirements',
  },
  {
    id: 'lost-document',
    title: 'I lost an immigration document',
    riskLevel: 'medium',
    description: 'Replacement procedures for lost documents',
    shortDescription: 'How to replace lost immigration documents',
  },
]

function ScenariosFallback() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="h-9 w-64 animate-pulse rounded-lg bg-sage-200" />
      <div className="mt-4 h-5 max-w-2xl animate-pulse rounded-lg bg-sage-200" />
      <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-2xl border border-sage-200 bg-cream-100" />
        ))}
      </div>
    </div>
  )
}

export default function ScenariosPage() {
  return (
    <Suspense fallback={<ScenariosFallback />}>
      <ScenariosContent />
    </Suspense>
  )
}

type RiskFilter = 'all' | Scenario['riskLevel']

function ScenariosContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [query, setQuery] = useState('')
  const [riskFilter, setRiskFilter] = useState<RiskFilter>('all')

  const requestedId = useMemo(() => searchParams.get('s'), [searchParams])

  const filteredScenarios = useMemo(() => {
    const q = query.trim().toLowerCase()
    return scenarios.filter((s) => {
      const matchesRisk = riskFilter === 'all' || s.riskLevel === riskFilter
      const matchesQuery =
        !q ||
        s.title.toLowerCase().includes(q) ||
        s.shortDescription.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q)
      return matchesRisk && matchesQuery
    })
  }, [query, riskFilter])

  useEffect(() => {
    if (!requestedId) return
    const match = scenarios.find((s) => s.id === requestedId)
    if (match) setSelectedScenario(match)
  }, [requestedId])

  const openScenario = (scenario: Scenario) => {
    setSelectedScenario(scenario)
    router.replace(`/scenarios?s=${encodeURIComponent(scenario.id)}`, { scroll: false })
  }

  const closeModal = () => {
    setSelectedScenario(null)
    router.replace('/scenarios', { scroll: false })
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        eyebrow="Guides"
        title="Scenario guides"
        description="Pick a situation to see an overview and next steps. These are general guides—consult an attorney for advice about your specific case."
      />

      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <label className="relative block w-full sm:max-w-md">
          <span className="sr-only">Search scenarios</span>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by topic…"
            className="w-full rounded-xl border border-sage-200 bg-cream-50 py-2.5 pl-10 pr-4 text-sm text-forest-900 shadow-sm transition-all duration-300 placeholder:text-sage-500 focus:-translate-y-0.5 focus:border-sage-400 focus:shadow-elevated focus:outline-none focus:ring-2 focus:ring-sage-400/30"
          />
          <svg
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-sage-500"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden
          >
            <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.8" />
            <path d="M20 20l-3-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </label>
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by risk level">
          {(['all', 'low', 'medium', 'high'] as const).map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => setRiskFilter(level)}
              className={`filter-pill ${
                riskFilter === level
                  ? level === 'all'
                    ? 'filter-pill-active'
                    : `filter-pill-active filter-pill-risk-${level}`
                  : 'filter-pill-inactive'
              }`}
            >
              {level === 'all' ? 'All' : level}
            </button>
          ))}
        </div>
      </div>

      {filteredScenarios.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-sage-300 bg-cream-50 px-6 py-12 text-center">
          <p className="text-lg font-semibold text-forest-900">No scenarios match</p>
          <p className="mt-2 text-sm text-sage-800">Try a different search term or clear the risk filter.</p>
          <button
            type="button"
            onClick={() => {
              setQuery('')
              setRiskFilter('all')
            }}
            className="mt-4 text-sm font-semibold text-sage-700 underline-offset-2 hover:underline"
          >
            Clear filters
          </button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredScenarios.map((scenario) => (
            <ScenarioCard key={scenario.id} scenario={scenario} onOpen={() => openScenario(scenario)} />
          ))}
        </div>
      )}

      {selectedScenario ? <ScenarioModal scenario={selectedScenario} onClose={closeModal} /> : null}
    </div>
  )
}

function ScenarioCard({ scenario, onOpen }: { scenario: Scenario; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="group interactive-card w-full p-6 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-500 focus-visible:ring-offset-2 focus-visible:ring-offset-cream-200"
    >
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-lg font-semibold text-forest-900 transition-colors duration-200 group-hover:text-sage-700">{scenario.title}</h3>
        <RiskBadge level={scenario.riskLevel} className="transition-transform duration-200 group-hover:scale-105" />
      </div>
      <p className="mt-3 text-sm leading-relaxed text-sage-800">{scenario.shortDescription}</p>
      <p className="mt-4 flex items-center gap-1 text-sm font-semibold text-sage-700 transition-colors duration-200 group-hover:text-sage-900">
        Open overview
        <span className="transition-transform duration-200 group-hover:translate-x-1">→</span>
      </p>
    </button>
  )
}

function ScenarioModal({ scenario, onClose }: { scenario: Scenario; onClose: () => void }) {
  const panelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    panelRef.current?.focus()
  }, [scenario.id])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-forest-950/60 p-4 backdrop-blur-[2px] transition-opacity duration-300"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="scenario-modal-title"
        tabIndex={-1}
        className="animate-modal-in max-h-[min(90vh,860px)] w-full max-w-2xl overflow-y-auto rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-2xl outline-none sm:p-8"
      >
        <div className="flex items-start justify-between gap-4">
          <h2 id="scenario-modal-title" className="text-2xl font-bold tracking-tight text-forest-900">
            {scenario.title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-sage-200 bg-cream-50 text-lg text-forest-900 transition hover:bg-cream-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-500"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="mt-4">
          <RiskBadge level={scenario.riskLevel} label={`${scenario.riskLevel} risk`} className="text-xs" />
        </div>

        <div className="mt-8 space-y-6">
          <section>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-sage-600">Situation</h3>
            <p className="mt-2 text-base leading-relaxed text-sage-900">{scenario.description}</p>
          </section>

          <div className="rounded-2xl border border-sage-200 bg-cream-100 p-5">
            <h3 className="text-base font-semibold text-forest-900">Important</h3>
            <p className="mt-2 text-sm leading-relaxed text-sage-900">
              This is a placeholder guide. Backend integration is pending. In the final version, this will include
              detailed legal information, rights, procedures, and official sources.
            </p>
          </div>

          <div className="rounded-2xl border border-sage-300 bg-sage-50 p-5">
            <h3 className="text-base font-semibold text-forest-900">Legal disclaimer</h3>
            <p className="mt-2 text-sm leading-relaxed text-forest-900/90">
              This is general legal information, not legal advice. Consult with an immigration attorney for your
              specific situation.
            </p>
          </div>
        </div>

        <div className="mt-8 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="btn-primary btn-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
