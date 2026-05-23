/** Types for POST /api/chat — mirrors backend ChatResponse (mobile-only). */

export type ChatCitation = {
  citation: string
  official_url?: string | null
  topic?: string | null
  subtopic?: string | null
  risk_level?: string | null
}

export type ChatUsedChunk = {
  rank: number
  chunk_id: number
  citation: string
  official_url?: string | null
  topic?: string | null
  subtopic?: string | null
  risk_level?: string | null
  hybrid_score: number
  snippet: string
}

export type ClarificationOption = {
  label: string
  value: string
}

export type ChatResponse = {
  status: string
  privacy_mode: string
  query_hash: string
  answer: string
  citations: ChatCitation[]
  disclaimer: string
  active_dataset?: string | null
  clarifying_question?: string | null
  options?: ClarificationOption[] | null
  used_chunks: ChatUsedChunk[]
  suggested_followups?: string[]
}

export type ChatClarificationContent = {
  answer: string
  clarifyingQuestion: string
  options: ClarificationOption[]
  disclaimer: string
  privacyMode: string
}

/** In-memory assistant payload shown in the Ask thread (never persisted). */
export type ChatAssistantContent = {
  answer: string
  citations: ChatCitation[]
  disclaimer: string
  privacyMode: string
  activeDataset?: string | null
  citationsMissing: boolean
  suggestedFollowups: string[]
}

export type ChatApiErrorCode = 'offline' | 'timeout' | 'http' | 'empty' | 'parse'
