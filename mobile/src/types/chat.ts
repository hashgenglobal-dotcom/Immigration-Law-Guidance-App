/** Types for POST /api/chat — mirrors backend StructuredResultResponse. */

export type LegalCitation = {
  title: string
  url: string
  snippet: string
}

export type ChatResponse = {
  ui_mode: 'result'
  short_answer: string
  eligibility_checklist: string[]
  next_steps: string[]
  citations: LegalCitation[]
  disclaimer: string
}

/** Used by ClarificationOptions UI (clarification flow is not yet active). */
export type ClarificationOption = {
  label: string
  value: string
}

/** In-memory assistant payload shown in the Ask thread (never persisted). */
export type ChatAssistantContent = {
  shortAnswer: string
  eligibilityChecklist: string[]
  nextSteps: string[]
  citations: LegalCitation[]
  disclaimer: string
  citationsMissing: boolean
}

export type ChatApiErrorCode = 'offline' | 'timeout' | 'http' | 'empty' | 'parse'
