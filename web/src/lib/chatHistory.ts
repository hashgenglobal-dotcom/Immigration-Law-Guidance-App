import type { ChatResponse } from './api'

const CHAT_HISTORY_KEY = 'sourcepath.chat.sessions.v1'
export const CHAT_HISTORY_UPDATED_EVENT = 'sourcepath:chat-history-updated'

export type StoredTurn =
  | { role: 'user'; text: string }
  | { role: 'assistant'; response: ChatResponse }
  | { role: 'assistant'; error: string }

export type ChatSession = {
  id: string
  title: string
  updatedAt: number
  turns: StoredTurn[]
}

function emitUpdated() {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(CHAT_HISTORY_UPDATED_EVENT))
}

function readRawSessions(): ChatSession[] {
  if (typeof window === 'undefined') return []
  const raw = window.localStorage.getItem(CHAT_HISTORY_KEY)
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter((item): item is ChatSession => {
        if (!item || typeof item !== 'object') return false
        const maybe = item as Partial<ChatSession>
        return (
          typeof maybe.id === 'string' &&
          typeof maybe.title === 'string' &&
          typeof maybe.updatedAt === 'number' &&
          Array.isArray(maybe.turns)
        )
      })
      .sort((a, b) => b.updatedAt - a.updatedAt)
  } catch {
    return []
  }
}

function writeSessions(sessions: ChatSession[]) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(sessions))
  emitUpdated()
}

export function getSessions(): ChatSession[] {
  return readRawSessions()
}

export function getSession(id: string): ChatSession | null {
  return readRawSessions().find((session) => session.id === id) ?? null
}

/** Insert or replace by session id (never duplicates the same id). */
export function saveSession(session: ChatSession): ChatSession[] {
  const sessions = readRawSessions()
  const index = sessions.findIndex((item) => item.id === session.id)
  if (index >= 0) {
    sessions[index] = session
  } else {
    sessions.push(session)
  }
  const next = sessions.sort((a, b) => b.updatedAt - a.updatedAt)
  writeSessions(next)
  return next
}

export function deleteSession(id: string): ChatSession[] {
  const next = readRawSessions().filter((session) => session.id !== id)
  writeSessions(next)
  return next
}
