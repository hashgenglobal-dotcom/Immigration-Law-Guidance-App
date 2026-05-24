/**
 * API helper placeholder.
 *
 * Reads VITE_API_BASE_URL from the environment. The backend does not need
 * to be running for the web app to start — callers should handle fetch errors
 * gracefully.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
}

export type ChatRequest = {
  message: string
  top_k?: number
  selected_category?: string | null
  conversation?: ChatMessage[]
}

export type ClarificationOption = {
  label: string
  value: string
}

export type ChatResponse =
  | {
      status: 'ok'
      answer: string
      citations: string[]
      suggested_followups?: string[]
    }
  | {
      status: 'needs_clarification'
      answer: string
      clarifying_question: string
      options: ClarificationOption[]
      citations: []
    }

export async function sendChatMessage(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<ChatResponse>
}
