const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type ChatRequest = {
  message: string
  top_k?: number
  selected_category?: string | null
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
      body: JSON.stringify(req),
    })
  } catch {
    throw new Error(
      'Backend is not reachable. Start the FastAPI backend and local Ollama services, then try again.',
    )
  }

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
