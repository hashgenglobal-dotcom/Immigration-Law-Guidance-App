import type { PrincipleAccent } from './aboutContentTypes'

export type { PrincipleAccent } from './aboutContentTypes'

export const ABOUT_MISSION = {
  eyebrow: 'Trust center',
  headline: 'Built for clarity. Grounded in truth.',
  lead:
    'U.S. immigration law was not written for easy reading—and unreliable advice spreads faster than the rules themselves. SourcePath helps you understand where you stand in plain language, always tied to what the government actually published.',
  body:
    'We search an indexed library of USCIS policy, the Code of Federal Regulations, and the Immigration and Nationality Act—then surface the passage that matters with a citation you can open and verify. We do not invent rules or improvise from model memory. You read the source, confirm it fits your facts, and take your next step—with a qualified attorney when your situation requires one.',
} as const

export const TRUST_PILLARS = [
  {
    icon: '📄',
    label: 'Cited',
    desc: 'Answers reference CFR, INA, and USCIS materials you can verify—not unchecked AI output.',
  },
  {
    icon: '🔒',
    label: 'Private',
    desc: 'Minimal data collection; session-focused design without selling your questions.',
  },
  {
    icon: '📚',
    label: 'Official',
    desc: 'Retrieval from government-indexed text—not model memory alone.',
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
    title: 'What SourcePath does',
    description:
      'Explains immigration topics in plain language, walks through common procedures, and points you to official sources—with citations you can check.',
    icon: '✓',
    accent: 'navy',
  },
  {
    title: 'What it does not do',
    description:
      'No legal advice, representation, or attorney–client relationship. Not for emergencies—contact a qualified attorney when you need case-specific counsel.',
    icon: '✕',
    accent: 'bronze',
  },
  {
    title: 'Privacy by design',
    description:
      'We prioritize minimal collection and transparent limits. Answers come from retrieved official text, not from remembering your past chats in a model.',
    icon: '🛡',
    accent: 'bronze',
  },
  {
    title: 'Official sources first',
    description:
      'When in doubt, read the linked regulation or agency page and confirm it matches your facts, dates, and immigration history.',
    icon: '📚',
    accent: 'navy',
  },
]

export const EXPLORE_ACTIONS = [
  { to: '/chat', icon: '💬', title: 'Ask a question', subtitle: 'Citation-first answers from the live corpus' },
  { to: '/scenarios', icon: '📚', title: 'Browse scenarios', subtitle: 'Step-by-step guides for common situations' },
  { to: '/sources', icon: '🔗', title: 'Source library', subtitle: 'Full catalog of indexed legal materials' },
] as const
