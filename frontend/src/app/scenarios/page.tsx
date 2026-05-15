'use client'

import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import PageHeader from '@/components/PageHeader'

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

function ScenariosContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)

  const requestedId = useMemo(() => searchParams.get('s'), [searchParams])

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

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {scenarios.map((scenario) => (
          <ScenarioCard key={scenario.id} scenario={scenario} onOpen={() => openScenario(scenario)} />
        ))}
      </div>

      {selectedScenario ? <ScenarioModal scenario={selectedScenario} onClose={closeModal} /> : null}
    </div>
  )
}

function ScenarioCard({ scenario, onOpen }: { scenario: Scenario; onOpen: () => void }) {
  const risk = {
    low: 'border-sage-200 bg-cream-100 text-forest-900',
    medium: 'border-sage-400 bg-sage-100 text-forest-900',
    high: 'border-forest-800 bg-forest-900 text-cream-100',
  }[scenario.riskLevel]

  return (
    <button
      type="button"
      onClick={onOpen}
      className="group w-full rounded-2xl border border-sage-200 bg-cream-50 p-6 text-left shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-sage-400 hover:shadow-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-500 focus-visible:ring-offset-2 focus-visible:ring-offset-cream-200"
    >
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-lg font-semibold text-forest-900 transition-colors duration-200 group-hover:text-sage-700">{scenario.title}</h3>
        <span
          className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide transition-transform duration-200 group-hover:scale-105 ${risk}`}
        >
          {scenario.riskLevel}
        </span>
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

  const risk = {
    low: 'border-sage-200 bg-cream-100 text-forest-900',
    medium: 'border-sage-400 bg-sage-100 text-forest-900',
    high: 'border-forest-800 bg-forest-900 text-cream-100',
  }[scenario.riskLevel]

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
        className="max-h-[min(90vh,860px)] w-full max-w-2xl animate-in fade-in zoom-in-95 slide-in-from-bottom-8 duration-300 overflow-y-auto rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-2xl outline-none sm:p-8"
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
          <span
            className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${risk}`}
          >
            {scenario.riskLevel} risk
          </span>
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
            className="inline-flex items-center justify-center rounded-xl bg-sage-500 px-5 py-2.5 text-sm font-semibold text-cream-50 shadow-sm transition hover:bg-sage-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-400 focus-visible:ring-offset-2 focus-visible:ring-offset-cream-50"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
