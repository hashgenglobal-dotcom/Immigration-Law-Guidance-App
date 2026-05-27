const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type ConversationTurn = {
  role: 'user' | 'assistant'
  content: string
}

const MAX_CONVERSATION_TURNS = 4
const MAX_ASSISTANT_CHARS = 300

function extractAssistantSummary(answer: string): string {
  const text = answer.trim()
  if (!text) return ''

  const shortMatch = text.match(
    /^Short answer\s*:\s*\n?([\s\S]*?)(?=\n(?:What this means|Typical next steps|Official sources|Important caution)\s*:|$)/im,
  )
  if (shortMatch?.[1]?.trim()) {
    return shortMatch[1].trim().slice(0, MAX_ASSISTANT_CHARS)
  }

  return text.replace(/\s+/g, ' ').trim().slice(0, MAX_ASSISTANT_CHARS)
}

export type ChatRequest = {
  message: string
  top_k?: number
  selected_category?: string | null
  /** Up to 4 prior in-session turns; processed in memory only. */
  conversation?: ConversationTurn[]
}

export type ClarificationOption = {
  label: string
  value: string
}

export type ChatCitation = {
  citation: string
  official_url: string | null
  topic: string | null
  subtopic: string | null
  risk_level: string | null
}

export type ChatUsedChunk = {
  rank: number
  chunk_id: number
  citation: string
  official_url: string | null
  topic: string | null
  subtopic: string | null
  risk_level: string | null
  hybrid_score: number
  snippet: string
  dataset_version: string | null
  source_family: string | null
}

export type ChatResponse =
  | {
      status: 'ok'
      privacy_mode: string
      query_hash: string
      answer: string
      citations: ChatCitation[]
      disclaimer: string
      active_dataset: string | null
      active_datasets: string[]
      mvp_sources: string[]
      clarifying_question: null
      options: null
      used_chunks: ChatUsedChunk[]
      suggested_followups?: string[]
    }
  | {
      status: 'needs_clarification'
      privacy_mode: string
      query_hash: string
      answer: string
      citations: ChatCitation[]
      disclaimer: string
      active_dataset: string | null
      active_datasets: string[]
      mvp_sources: string[]
      clarifying_question: string
      options: ClarificationOption[]
      used_chunks: ChatUsedChunk[]
      suggested_followups?: string[]
    }

export type FormattedAnswerSection = {
  title: string
  body: string
}

const STRUCTURED_SECTIONS = [
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

  if (sections.length > 0) return sections
  return [{ title: 'Information', body: text }]
}

export function hasStructuredSections(answer: string): boolean {
  return parseFormattedAnswer(answer).some((s) =>
    STRUCTURED_SECTIONS.includes(s.title as (typeof STRUCTURED_SECTIONS)[number]),
  )
}

type ChatStreamEvent =
  | { type: 'token'; delta: string }
  | { type: 'done'; response: ChatResponse }
  | { type: 'error'; error_code?: string; message?: string }

function buildChatRequestBody(req: ChatRequest): string {
  return JSON.stringify(req)
}

function parseSseEvents(buffer: string): { events: unknown[]; remainder: string } {
  const events: unknown[] = []
  const parts = buffer.split('\n\n')
  const remainder = parts.pop() ?? ''
  for (const part of parts) {
    const line = part.split('\n').find((l) => l.startsWith('data:'))
    if (!line) continue
    const jsonText = line.slice(5).trim()
    if (!jsonText) continue
    try {
      events.push(JSON.parse(jsonText))
    } catch {
      /* ignore partial frames */
    }
  }
  return { events, remainder }
}

function isOkChatStatus(status: string | undefined): boolean {
  return status === 'ok' || status === 'success' || status === 'needs_clarification'
}

/** Prior visible turns for in-session memory (never persisted beyond one request). */
export function buildAskConversationPayload(turns: unknown[]): ConversationTurn[] {
  const out: ConversationTurn[] = []

  for (const raw of turns) {
    if (!raw || typeof raw !== 'object') continue
    const turn = raw as Record<string, unknown>

    if (turn.role === 'user' && typeof turn.text === 'string') {
      out.push({ role: 'user', content: turn.text.slice(0, 400) })
      continue
    }

    if (turn.role !== 'assistant' || !('response' in turn)) continue
    const response = turn.response as ChatResponse
    const summary = extractAssistantSummary(response.answer)
    if (summary) {
      out.push({ role: 'assistant', content: summary.slice(0, MAX_ASSISTANT_CHARS) })
    }
  }

  return out.slice(-MAX_CONVERSATION_TURNS)
}

type FastAPIErrorDetail = {
  error_code?: string
  message?: string
  privacy_mode?: string
}

export async function sendChatMessage(req: ChatRequest): Promise<ChatResponse> {
  let res: Response
  try {
    res = await fetch(`${BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: buildChatRequestBody(req),
    })
  } catch {
    throw new Error(
      'Backend is not reachable. Start the FastAPI backend and local Ollama services, then try again.',
    )
  }

  return parseChatResponse(res)
}

/** Prefer POST /api/chat/stream; falls back to /api/chat if streaming is unavailable. */
export async function sendChatMessagePreferStream(
  req: ChatRequest,
  onToken?: (accumulated: string) => void,
): Promise<ChatResponse> {
  let res: Response
  try {
    res = await fetch(`${BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        Accept: 'text/event-stream',
        'Content-Type': 'application/json',
      },
      body: buildChatRequestBody(req),
    })
  } catch {
    return sendChatMessage(req)
  }

  if (!res.ok) {
    return sendChatMessage(req)
  }

  const reader = res.body?.getReader?.()
  if (!reader) {
    return sendChatMessage(req)
  }

  const decoder = new TextDecoder()
  let buffer = ''
  let accumulated = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const { events, remainder } = parseSseEvents(buffer)
      buffer = remainder

      for (const raw of events) {
        const event = raw as ChatStreamEvent
        if (event.type === 'token' && typeof event.delta === 'string') {
          accumulated += event.delta
          onToken?.(accumulated)
        } else if (event.type === 'error') {
          throw new Error(event.message ?? 'An error occurred. Please try again.')
        } else if (event.type === 'done' && event.response) {
          const data = event.response
          if (!isOkChatStatus(data.status)) {
            throw new Error('An error occurred. Please try again.')
          }
          if (data.status !== 'needs_clarification' && !data.answer?.trim()) {
            throw new Error('No answer was returned. Please try again.')
          }
          return data
        }
      }
    }
  } catch (err) {
    if (err instanceof Error) throw err
    return sendChatMessage(req)
  }

  return sendChatMessage(req)
}

async function parseChatResponse(res: Response): Promise<ChatResponse> {
  if (!res.ok) {
    let detail: FastAPIErrorDetail | null = null
    try {
      const body = (await res.json()) as { detail?: FastAPIErrorDetail | string }
      if (body?.detail && typeof body.detail === 'object') {
        detail = body.detail as FastAPIErrorDetail
      }
    } catch { /* json parse failed */ }

    if (
      detail?.error_code === 'CHAT_MODEL_UNAVAILABLE' ||
      detail?.error_code === 'CHAT_RETRIEVAL_UNAVAILABLE'
    ) {
      throw new Error(
        detail.message ?? 'Local model service unavailable. Ensure Ollama is running: ollama serve',
      )
    }
    if (detail?.error_code === 'CHAT_ERROR') {
      throw new Error(detail.message ?? 'An internal error occurred during response generation.')
    }
    throw new Error('An error occurred. Please try again.')
  }

  return res.json() as Promise<ChatResponse>
}
