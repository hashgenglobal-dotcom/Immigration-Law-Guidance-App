import Link from 'next/link'
import { RiskBadge } from '@/components/RiskBadge'
import { ScrollReveal } from '@/components/ScrollReveal'
import { Button } from '@/components/ui/button'
import { Hero1 } from '@/components/ui/hero-1'

const features = [
  {
    title: 'Ask questions',
    description: 'Plain-language explanations about immigration topics and your rights.',
    icon: (
      <svg className="icon-pop h-6 w-6" viewBox="0 0 24 24" fill="none" aria-hidden>
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
      <svg className="icon-pop h-6 w-6" viewBox="0 0 24 24" fill="none" aria-hidden>
        <path d="M7 11V8a5 5 0 0 1 10 0v3" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
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
      <svg className="icon-pop h-6 w-6" viewBox="0 0 24 24" fill="none" aria-hidden>
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

      <section className="border-b border-sage-200/80 bg-cream-100/60 py-6">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-3 px-4 sm:px-6 lg:px-8">
          {[
            { href: '/ask', label: 'Ask a question' },
            { href: '/scenarios', label: 'Browse scenarios' },
            { href: '/about', label: 'About & privacy' },
          ].map((item) => (
            <Link key={item.href} href={item.href} className="pill-link">
              {item.label}
              <span aria-hidden className="pill-arrow text-sage-600 transition-transform duration-300">
                →
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="border-b border-sage-200/80 bg-cream-50 py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <ScrollReveal className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-forest-900">How it works</h2>
            <p className="mt-3 text-lg text-sage-800">
              Three principles behind the experience: clarity, privacy, and citations.
            </p>
          </ScrollReveal>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {features.map((f, i) => (
              <ScrollReveal key={f.title} delay={i * 100}>
                <div className="group interactive-card h-full p-6">
                  <div className="inline-flex rounded-xl bg-gradient-to-br from-sage-500 to-sage-600 p-3 text-cream-50 shadow-glow-gold">
                    {f.icon}
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-forest-900">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-sage-800">{f.description}</p>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <ScrollReveal className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-forest-900">Common scenarios</h2>
            <p className="mt-3 text-lg text-sage-800">
              Short guides for frequent situations—always confirm facts with official sources and counsel when needed.
            </p>
          </ScrollReveal>

          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[
              { scenarioId: 'ice-door', title: 'ICE came to my door', riskLevel: 'high' as const, description: 'Know your rights when immigration officers arrive' },
              { scenarioId: 'overstay', title: 'I overstayed my visa', riskLevel: 'medium' as const, description: 'Understanding your options after visa expiration' },
              { scenarioId: 'nta', title: 'I received a Notice to Appear', riskLevel: 'high' as const, description: 'What to do when placed in removal proceedings' },
              { scenarioId: 'asylum', title: 'I want to apply for asylum', riskLevel: 'medium' as const, description: 'Asylum application process and requirements' },
              { scenarioId: 'citizenship', title: 'I want to apply for citizenship', riskLevel: 'low' as const, description: 'Naturalization process for permanent residents' },
              { scenarioId: 'lost-document', title: 'I lost an immigration document', riskLevel: 'medium' as const, description: 'How to replace lost immigration documents' },
            ].map((s, i) => (
              <ScrollReveal key={s.scenarioId} delay={i * 80}>
                <ScenarioCard {...s} />
              </ScrollReveal>
            ))}
          </div>

          <ScrollReveal className="mt-10 text-center" delay={200}>
            <Button href="/scenarios" size="md">
              View all scenarios
            </Button>
          </ScrollReveal>
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
  return (
    <Link
      href={`/scenarios?s=${encodeURIComponent(scenarioId)}`}
      className="group interactive-card block p-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-500 focus-visible:ring-offset-2 focus-visible:ring-offset-cream-200"
    >
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-lg font-semibold text-forest-900 transition-colors duration-300 group-hover:text-sage-700">
          {title}
        </h3>
        <RiskBadge level={riskLevel} className="transition-transform duration-300 group-hover:scale-105" />
      </div>
      <p className="mt-3 text-sm leading-relaxed text-sage-800">{description}</p>
      <p className="mt-4 flex items-center gap-1 text-sm font-semibold text-sage-700 transition-colors duration-300 group-hover:text-sage-900">
        Open guide
        <span className="transition-transform duration-300 group-hover:translate-x-1" aria-hidden>
          →
        </span>
      </p>
    </Link>
  )
}
