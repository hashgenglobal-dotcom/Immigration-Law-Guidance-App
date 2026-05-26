import type { PrincipleAccent } from './aboutContentTypes'
import { PRODUCT_CATEGORY } from './productMessaging'

export type { PrincipleAccent } from './aboutContentTypes'

export const ABOUT_MISSION = {
  eyebrow: 'Why SourcePath',
  headline: 'Built for clarity. Grounded in truth.',
  category: PRODUCT_CATEGORY,
  lead:
    'U.S. immigration law was not written for easy reading—and unreliable advice spreads faster than the rules themselves. SourcePath helps you understand where you stand in plain language, always tied to what the government actually published.',
  body:
    'We search an indexed library of USCIS policy, the Code of Federal Regulations, and the Immigration and Nationality Act—then surface the passage that matters with a citation you can open and verify. We do not invent rules or improvise from model memory. You read the source, confirm it fits your facts, and take your next step—with a qualified attorney when your situation requires one.',
} as const

export const TRUST_PILLARS = [
  {
    icon: '✓',
    label: 'Verifiable',
    desc: 'Every claim ties to a retrieved statute, regulation, or agency source you can open.',
  },
  {
    icon: '🔒',
    label: 'Private',
    desc: 'Minimal data collection; session-focused design without selling your questions.',
  },
  {
    icon: '📚',
    label: 'Official',
    desc: 'Navigation over government-indexed corpora—not open-ended chat guesswork.',
    linkTo: '/sources#catalog',
  },
] as const

export const ABOUT_PRINCIPLES: {
  title: string
  description: string
  icon: string
  accent: PrincipleAccent
}[] = [
  {
    title: 'How navigation works',
    description:
      'Retrieve official passages from our indexed corpus → cite the source inline → explain in plain language you can verify on USCIS.gov or eCFR.',
    icon: '⟳',
    accent: 'navy',
  },
  {
    title: 'Routine vs. complex matters',
    description:
      'Clear, cited orientation for common questions. High-stakes situations (removal, fraud, criminal history) may need a qualified attorney—we surface that boundary, not hide behind disclaimers.',
    icon: '◎',
    accent: 'navy',
  },
  {
    title: 'What we do not provide',
    description:
      'No legal advice, representation, or attorney–client relationship. Not for emergencies—contact counsel when you need case-specific strategy.',
    icon: '✕',
    accent: 'bronze',
  },
  {
    title: 'Privacy by design',
    description:
      'Answers come from retrieved official text in your session—not from a model remembering your history across users.',
    icon: '🛡',
    accent: 'bronze',
  },
]

export const EXPLORE_ACTIONS = [
  { to: '/chat', icon: '💬', title: 'Ask a question', subtitle: 'Retrieve, cite, and explain from the live corpus' },
  { to: '/scenarios', icon: '📚', title: 'Browse scenarios', subtitle: 'Structured paths for common situations' },
  { to: '/sources', icon: '🔗', title: 'Source library', subtitle: 'Browse indexed CFR, INA, and USCIS materials' },
] as const
