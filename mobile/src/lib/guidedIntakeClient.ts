/**
 * Client-side category hints for typed clarification (mirrors backend rules).
 * Used only to set selected_category on the next request — answers still come from the API.
 */

const PHRASE_RULES: { pattern: RegExp; value: string }[] = [
  { pattern: /\bf-?1\b.*\b(opt|stem)\b/i, value: 'f1_opt_stem_opt' },
  { pattern: /\b(stem\s+)?opt\b/i, value: 'f1_opt_stem_opt' },
  { pattern: /\bpending asylum\b/i, value: 'asylum_pending' },
  { pattern: /\bi-?485\b.*\bpending\b/i, value: 'adjustment_pending' },
  { pattern: /\btps\b/i, value: 'tps' },
  { pattern: /\bdaca\b/i, value: 'daca' },
  { pattern: /\baffirmative asylum\b/i, value: 'asylum_eligibility' },
  { pattern: /\bimmigration court\b|\bremoval proceedings\b/i, value: 'asylum_defensive' },
  { pattern: /\bfamily[- ]based\b|\bi-?130\b/i, value: 'aos_family' },
  { pattern: /\bemployment[- ]based\b/i, value: 'aos_employment' },
  { pattern: /\bnaturalization\b|\bn-?400\b/i, value: 'naturalization_residence' },
  { pattern: /\badvance parole\b/i, value: 'travel_aos' },
]

export function resolveCategoryFromTypedReply(text: string): string | null {
  const trimmed = text.trim()
  if (!trimmed) return null
  const lower = trimmed.toLowerCase()
  for (const { pattern, value } of PHRASE_RULES) {
    if (pattern.test(trimmed)) return value
  }
  if (lower.includes('f-1') && lower.includes('opt')) return 'f1_opt_stem_opt'
  if (lower.includes('pending asylum')) return 'asylum_pending'
  return null
}
