import { extractShortAnswer } from '@/lib/parseFormattedAnswer'
import type { ChatAssistantContent } from '@/types/chat'

export type ConversationTurnPayload = {
  role: 'user' | 'assistant'
  content: string
}

const MAX_TURNS = 6
const MAX_ASSISTANT_CHARS = 400

/** Build API conversation payload from visible Ask turns (in-memory only). */
export function buildConversationPayload(turns: unknown[]): ConversationTurnPayload[] {
  const out: ConversationTurnPayload[] = []
  for (const raw of turns) {
    if (!raw || typeof raw !== 'object') continue
    const turn = raw as Record<string, unknown>
    if (turn.role === 'user' && typeof turn.text === 'string') {
      out.push({ role: 'user', content: turn.text.slice(0, 500) })
      continue
    }
    if (turn.role !== 'assistant') continue
    if ('content' in turn && turn.content && typeof turn.content === 'object') {
      const content = turn.content as ChatAssistantContent
      const sections = extractShortAnswer(content.answer)
      const short =
        sections.trim() ||
        content.answer.replace(/\s+/g, ' ').trim().slice(0, MAX_ASSISTANT_CHARS)
      out.push({ role: 'assistant', content: short.slice(0, MAX_ASSISTANT_CHARS) })
      continue
    }
    if ('clarification' in turn && turn.clarification && typeof turn.clarification === 'object') {
      const clar = turn.clarification as { answer?: string }
      const intro = (clar.answer ?? '').trim().slice(0, MAX_ASSISTANT_CHARS)
      if (intro) out.push({ role: 'assistant', content: intro })
    }
  }
  return out.slice(-MAX_TURNS)
}
