import Link from 'next/link'
import { MessageCircle, Library } from 'lucide-react'

const ACTIONS = [
  {
    id: 'ask',
    title: 'Ask a question',
    subtitle: 'Chat with the assistant—plain language, citation-first answers.',
    href: '/ask',
    icon: MessageCircle,
  },
  {
    id: 'scenarios',
    title: 'Browse scenarios',
    subtitle: 'Step-by-step guides for common immigration situations.',
    href: '/scenarios',
    icon: Library,
  },
] as const

export function HomeExploreSection() {
  return (
    <section id="home-explore-section" className="mt-8">
      <div className="mb-5 flex items-start gap-3">
        <div className="w-1 shrink-0 self-stretch min-h-9 rounded-sm bg-navy-800" aria-hidden />
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-bronze-500">Explore</p>
          <h2 className="font-heading text-base font-semibold tracking-tight text-navy-800 sm:text-lg">
            Where would you like to go?
          </h2>
        </div>
      </div>

      <ul className="flex flex-col gap-3" role="menu">
        {ACTIONS.map((action) => (
          <li key={action.id} role="none">
            <Link
              href={action.href}
              role="menuitem"
              className="group interactive-card flex items-start gap-4 p-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bronze-500"
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-bronze-200 bg-bronze-tint text-bronze-600 transition group-hover:bg-bronze-500 group-hover:text-parchment-50">
                <action.icon className="h-5 w-5" aria-hidden />
              </span>
              <span className="min-w-0 flex-1">
                <span className="font-heading text-base font-semibold text-navy-800">{action.title}</span>
                <span className="mt-1 block text-sm leading-relaxed text-bronze-700">{action.subtitle}</span>
              </span>
              <span className="mt-1 text-bronze-500 transition group-hover:translate-x-0.5" aria-hidden>
                →
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  )
}
