import type { ChatAssistantContent } from '@/types/chat'
import { parseFormattedAnswer } from '@/lib/parseFormattedAnswer'

export type ConversationTurnPayload = {
  role: 'user' | 'assistant'
  content: string
}

const MAX_TURNS = 4
const MAX_ASSISTANT_CHARS = 300

/**
 * Build in-memory conversation for the next /api/chat request.
 * Never persisted to AsyncStorage or the backend beyond the single request.
 */
export function buildAskConversationPayload(turns: unknown[]): ConversationTurnPayload[] {
  const out: ConversationTurnPayload[] = []

  for (const raw of turns) {
    if (!raw || typeof raw !== 'object') continue
    const turn = raw as Record<string, unknown>
    if (turn.role === 'user' && typeof turn.text === 'string') {
      out.push({ role: 'user', content: turn.text.slice(0, 400) })
      continue
    }
    if (turn.role !== 'assistant' || !('content' in turn)) continue
    const content = turn.content as ChatAssistantContent
    const sections = parseFormattedAnswer(content.answer)
    const short = sections.find((s) => s.title === 'Short answer')?.body.trim()
    const summary =
      short || content.answer.replace(/\s+/g, ' ').trim().slice(0, MAX_ASSISTANT_CHARS)
    if (summary) {
      out.push({ role: 'assistant', content: summary.slice(0, MAX_ASSISTANT_CHARS) })
    }
  }

  return out.slice(-MAX_TURNS)
}
