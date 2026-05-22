/** Parse backend structured answer text into mobile-friendly sections. */

export type FormattedAnswerSection = {
  title: string
  body: string
}

const SECTION_ORDER = [
  'Short answer',
  'What this means',
  'Typical next steps',
  'Official sources',
  'Important caution',
] as const

const HEADER_PATTERN =
  /^(Short answer|What this means|Typical next steps|Official sources|Important caution)\s*:\s*$/im

export function parseFormattedAnswer(answer: string): FormattedAnswerSection[] {
  const text = answer.trim()
  if (!text) return []

  const lines = text.split('\n')
  const sections: FormattedAnswerSection[] = []
  let currentTitle: string | null = null
  let bodyLines: string[] = []

  const flush = () => {
    if (!currentTitle) return
    const body = bodyLines.join('\n').trim()
    if (body) sections.push({ title: currentTitle, body })
    bodyLines = []
  }

  for (const line of lines) {
    const match = line.trim().match(HEADER_PATTERN)
    if (match) {
      flush()
      currentTitle = match[1]
      continue
    }
    if (currentTitle) bodyLines.push(line)
  }
  flush()

  if (sections.length > 0) {
    return sections
  }

  return [{ title: 'Information', body: text }]
}

export function hasStructuredSections(answer: string): boolean {
  return parseFormattedAnswer(answer).some((s) =>
    SECTION_ORDER.includes(s.title as (typeof SECTION_ORDER)[number]),
  )
}

/** Compact assistant text for multi-turn API context. */
export function extractShortAnswer(answer: string): string {
  const sections = parseFormattedAnswer(answer)
  const short = sections.find((s) => s.title === 'Short answer')
  return short?.body.trim() ?? ''
}
