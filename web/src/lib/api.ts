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

export type LegalCitation = {
  title: string
  url: string
  snippet: string
}

export type StructuredResultResponse = {
  ui_mode: 'result'
  short_answer: string
  eligibility_checklist: string[]
  next_steps: string[]
  citations: LegalCitation[]
  disclaimer: string
}

export type ChatResponse = StructuredResultResponse

function buildChatRequestBody(req: ChatRequest): string {
  return JSON.stringify(req)
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
    const summary = extractAssistantSummary(response.short_answer)
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

/** Legacy helper kept for compatibility; now uses structured /api/chat only. */
export async function sendChatMessagePreferStream(
  req: ChatRequest,
  _onToken?: (accumulated: string) => void,
): Promise<ChatResponse> {
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

  const data = (await res.json()) as ChatResponse
  if (data.ui_mode !== 'result') {
    throw new Error('Unexpected chat response format from backend.')
  }
  return data
}
