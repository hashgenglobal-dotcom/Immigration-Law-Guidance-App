import { CHAT_REQUEST_TIMEOUT_MS, getApiBaseUrl } from '@/constants/api'
import type { ChatAssistantContent, ChatClarificationContent, ChatResponse } from '@/types/chat'

export type ChatApiErrorCode = 'offline' | 'timeout' | 'http' | 'empty' | 'parse'

export class ChatApiError extends Error {
  readonly code: ChatApiErrorCode

  constructor(code: ChatApiErrorCode, message: string) {
    super(message)
    this.name = 'ChatApiError'
    this.code = code
  }
}

const OFFLINE_MESSAGE =
  'Could not connect to the guidance service. Please check the backend and try again.'
const TIMEOUT_MESSAGE = 'The request took too long. Please try again.'
const EMPTY_ANSWER_MESSAGE =
  'No answer was returned. Please try again or consult official sources and a qualified immigration attorney.'
const GENERIC_HTTP_MESSAGE =
  'The guidance service could not complete your request. Please try again later.'

function isOkStatus(status: string | undefined): boolean {
  return status === 'ok' || status === 'success' || status === 'needs_clarification'
}

function parseErrorDetail(body: unknown): string | null {
  if (!body || typeof body !== 'object') return null
  const detail = (body as { detail?: unknown }).detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && 'message' in detail) {
    const msg = (detail as { message?: unknown }).message
    if (typeof msg === 'string') return msg
  }
  return null
}

/**
 * Send a single question to POST /api/chat. Message is not logged or persisted.
 */
export async function sendChatMessage(
  message: string,
  topK = 5,
  selectedCategory?: string | null,
): Promise<ChatResponse> {
  const baseUrl = getApiBaseUrl()
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), CHAT_REQUEST_TIMEOUT_MS)

  let response: Response
  try {
    response = await fetch(`${baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        top_k: topK,
        ...(selectedCategory ? { selected_category: selectedCategory } : {}),
      }),
      signal: controller.signal,
    })
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ChatApiError('timeout', TIMEOUT_MESSAGE)
    }
    throw new ChatApiError('offline', OFFLINE_MESSAGE)
  } finally {
    clearTimeout(timeoutId)
  }

  let body: unknown
  try {
    body = await response.json()
  } catch {
    if (!response.ok) {
      throw new ChatApiError('http', GENERIC_HTTP_MESSAGE)
    }
    throw new ChatApiError('parse', GENERIC_HTTP_MESSAGE)
  }

  if (!response.ok) {
    const detail = parseErrorDetail(body)
    throw new ChatApiError('http', detail ?? GENERIC_HTTP_MESSAGE)
  }

  const data = body as ChatResponse
  if (!isOkStatus(data.status)) {
    throw new ChatApiError('http', GENERIC_HTTP_MESSAGE)
  }

  if (data.status !== 'needs_clarification' && !data.answer?.trim()) {
    throw new ChatApiError('empty', EMPTY_ANSWER_MESSAGE)
  }

  return data
}

export function toClarificationContent(data: ChatResponse): ChatClarificationContent {
  const options = Array.isArray(data.options) ? data.options : []
  return {
    answer: data.answer?.trim() || '',
    clarifyingQuestion: data.clarifying_question?.trim() || 'Which category best matches you?',
    options,
    disclaimer: data.disclaimer?.trim() || '',
    privacyMode: data.privacy_mode || 'local-first',
  }
}

export function toAssistantContent(data: ChatResponse): ChatAssistantContent {
  const citations = Array.isArray(data.citations) ? data.citations : []
  return {
    answer: data.answer.trim(),
    citations,
    disclaimer: data.disclaimer?.trim() || '',
    privacyMode: data.privacy_mode || 'local-first',
    activeDataset: data.active_dataset ?? null,
    citationsMissing: citations.length === 0,
  }
}
