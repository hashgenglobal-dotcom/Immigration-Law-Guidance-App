import Link from 'next/link'
import { Hero1 } from '@/components/ui/hero-1'

const features = [
  {
    title: 'Ask questions',
    description: 'Plain-language explanations about immigration topics and your rights.',
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path
          d="M12 18a6 6 0 1 0-6-6c0 1.4.5 2.7 1.3 3.7L7 19l3.3-1.3A5.9 5.9 0 0 0 12 18Z"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinejoin="round"
        />
        <path d="M8.5 9.5h.01M12 9.5h.01M15.5 9.5h.01" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    title: 'Privacy-first',
    description: 'Designed for local processing and minimal retention—no cloud AI calls for your personal facts.',
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path
          d="M7 11V8a5 5 0 0 1 10 0v3"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinecap="round"
        />
        <path
          d="M6 11h12v9a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-9Z"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    title: 'Official sources',
    description: 'Information is meant to be tied to USCIS, eCFR, INA, and other authoritative materials—not model memory.',
    icon: (
      <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path
          d="M7 4h10a2 2 0 0 1 2 2v14l-7-3-7 3V6a2 2 0 0 1 2-2Z"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
] as const

export default function HomePage() {
  return (
    <div>
      <Hero1 />

      <section className="border-b border-sage-200/80 bg-cream-50 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-forest-900">How it works</h2>
            <p className="mt-3 text-lg text-sage-800">
              Three principles behind the experience: clarity, privacy, and citations.
            </p>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="rounded-2xl border border-sage-200 bg-cream-100/90 p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-sage-300 hover:shadow-md"
              >
                <div className="inline-flex rounded-xl bg-sage-500 p-3 text-cream-50 shadow-sm">{f.icon}</div>
                <h3 className="mt-4 text-lg font-semibold text-forest-900">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-sage-800">{f.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-forest-900">Common scenarios</h2>
            <p className="mt-3 text-lg text-sage-800">
              Short guides for frequent situations—always confirm facts with official sources and counsel when needed.
            </p>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <ScenarioCard
              scenarioId="ice-door"
              title="ICE came to my door"
              riskLevel="high"
              description="Know your rights when immigration officers arrive"
            />
            <ScenarioCard
              scenarioId="overstay"
              title="I overstayed my visa"
              riskLevel="medium"
              description="Understanding your options after visa expiration"
            />
            <ScenarioCard
              scenarioId="nta"
              title="I received a Notice to Appear"
              riskLevel="high"
              description="What to do when placed in removal proceedings"
            />
            <ScenarioCard
              scenarioId="asylum"
              title="I want to apply for asylum"
              riskLevel="medium"
              description="Asylum application process and requirements"
            />
            <ScenarioCard
              scenarioId="citizenship"
              title="I want to apply for citizenship"
              riskLevel="low"
              description="Naturalization process for permanent residents"
            />
            <ScenarioCard
              scenarioId="lost-document"
              title="I lost an immigration document"
              riskLevel="medium"
              description="How to replace lost immigration documents"
            />
          </div>

          <div className="mt-10 text-center">
            <Link
              href="/scenarios"
              className="inline-flex items-center justify-center rounded-xl bg-sage-500 px-6 py-3 text-sm font-semibold text-cream-50 shadow-sm transition hover:bg-sage-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-400 focus-visible:ring-offset-2 focus-visible:ring-offset-cream-50"
            >
              View all scenarios
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

function ScenarioCard({
  scenarioId,
  title,
  riskLevel,
  description,
}: {
  scenarioId: string
  title: string
  riskLevel: 'low' | 'medium' | 'high'
  description: string
}) {
  const risk = {
    low: 'border-sage-200 bg-cream-100 text-forest-900',
    medium: 'border-sage-400 bg-sage-100 text-forest-900',
    high: 'border-forest-800 bg-forest-900 text-cream-100',
  }[riskLevel]

  return (
    <Link
      href={`/scenarios?s=${encodeURIComponent(scenarioId)}`}
      className="group block rounded-2xl border border-sage-200 bg-cream-50 p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-sage-400 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-500 focus-visible:ring-offset-2 focus-visible:ring-offset-cream-200"
    >
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-lg font-semibold text-forest-900 group-hover:text-sage-800">{title}</h3>
        <span className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${risk}`}>
          {riskLevel}
        </span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-sage-800">{description}</p>
      <p className="mt-4 text-sm font-semibold text-sage-700">
        Open guide <span aria-hidden>→</span>
      </p>
    </Link>
  )
}
