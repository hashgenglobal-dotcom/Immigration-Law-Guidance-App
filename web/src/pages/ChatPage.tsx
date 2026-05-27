import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import StructuredResultCard from '../components/chat/StructuredResultCard'
import DashboardLayout from '../components/layout/DashboardLayout'
import { buildAskConversationPayload, sendChatMessage } from '../lib/api'
import type { ChatResponse, LegalCitation } from '../lib/api'
import { getSession, saveSession, type StoredTurn } from '../lib/chatHistory'
import {
  CHAT_EMPTY_BODY,
  CHAT_EMPTY_TITLE,
  CHAT_HEADER_SUBTITLE,
  PRODUCT_LEGAL_LINE,
  PRODUCT_MOAT_LINE,
} from '../lib/productMessaging'
import styles from './ChatPage.module.css'

type Turn =
  | { id: number; role: 'user'; text: string }
  | { id: number; role: 'assistant'; response: ChatResponse }
  | { id: number; role: 'assistant'; pending: true }
  | { id: number; role: 'assistant'; error: string }

let _id = 0
function nextId() { return ++_id }
function nextSessionId() {
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function buildSessionTitle(message: string): string {
  const words = message.trim().split(/\s+/).filter(Boolean)
  return words.slice(0, 5).join(' ') || 'New conversation'
}

function toStoredTurns(turns: Turn[]): StoredTurn[] {
  const out: StoredTurn[] = []
  for (const turn of turns) {
    if (turn.role === 'user') out.push({ role: 'user', text: turn.text })
    if ('response' in turn) out.push({ role: 'assistant', response: turn.response })
    else if ('error' in turn) out.push({ role: 'assistant', error: turn.error })
  }
  return out
}

function hydrateSources(turns: Turn[]) {
  const assistantWithResponse = [...turns]
    .reverse()
    .find((turn): turn is Extract<Turn, { role: 'assistant'; response: ChatResponse }> =>
      turn.role === 'assistant' && 'response' in turn,
    )
  if (!assistantWithResponse) {
    return { citations: [] as LegalCitation[], hasResponse: false }
  }
  return {
    citations: assistantWithResponse.response.citations,
    hasResponse: true,
  }
}

const SUGGESTED_QUESTIONS = [
  'How do I apply for an EAD as an asylum applicant?',
  'Can I travel while my I-485 is pending?',
  'What happens after I receive a Notice to Appear?',
  'What are the naturalization requirements?',
]

const SAMPLE_SOURCE_GROUPS = [
  {
    type: 'Regulation',
    color: 'var(--blue)',
    colorTint: 'var(--blue-tint)',
    items: [
      { name: '8 CFR § 274a.12', desc: 'Employment authorization classes' },
      { name: '8 CFR § 208.7', desc: 'EAD filing window for asylum applicants' },
    ],
  },
  {
    type: 'USCIS Policy',
    color: 'var(--bronze)',
    colorTint: 'var(--bronze-tint)',
    items: [
      { name: 'Policy Manual Vol. 10', desc: 'Employment authorization procedures' },
    ],
  },
  {
    type: 'Form',
    color: '#2d6a2d',
    colorTint: '#eef6ee',
    items: [
      { name: 'Form I-765', desc: 'Application for Employment Authorization' },
    ],
  },
  {
    type: 'Statute',
    color: '#5b4db5',
    colorTint: '#f4f0fb',
    items: [
      { name: 'INA § 274A', desc: 'Unlawful employment of aliens' },
    ],
  },
]

type SourcesPanelProps = {
  citations: LegalCitation[]
  loading: boolean
  hasResponse: boolean
}

function SourcesPanel({ citations, loading, hasResponse }: SourcesPanelProps) {
  const hasCitations = citations.length > 0

  return (
    <div className={styles.sourcesPanel}>
      <div className={styles.sourcesHeader}>
        Latest answer sources
        {!loading && hasCitations && (
          <span style={{ fontWeight: 400, color: 'var(--text-secondary)', fontSize: 12, marginLeft: 8 }}>
            {citations.length} cited
          </span>
        )}
      </div>

      {/* Loading state */}
      {loading && (
        <p className={styles.sourcesExplainer} style={{ fontStyle: 'normal' }}>
          Retrieving sources…
        </p>
      )}

      {/* Initial state: no response yet */}
      {!loading && !hasResponse && (
        <>
          <p className={styles.sourcesExplainer}>
            Retrieved statutes, regulations, and agency sources appear here with every answer—open any citation
            to verify.
          </p>
          <div className={styles.sourcesScroll}>
            {SAMPLE_SOURCE_GROUPS.map((group) => (
              <div key={group.type} className={styles.sourceGroup}>
                <div
                  className={styles.sourceGroupLabel}
                  style={{ color: group.color, background: group.colorTint }}
                >
                  {group.type}
                </div>
                {group.items.map((item) => (
                  <div key={item.name} className={styles.sourceCard}>
                    <div className={styles.sourceName}>{item.name}</div>
                    <div className={styles.sourceDesc}>{item.desc}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </>
      )}

      {/* Empty state: response returned with no citations */}
      {!loading && hasResponse && !hasCitations && (
        <p className={styles.sourcesExplainer} style={{ fontStyle: 'normal', color: 'var(--text-secondary)' }}>
          No citations returned for this response.
        </p>
      )}

      {/* Real citations from latest answer */}
      {!loading && hasResponse && hasCitations && (
        <div className={styles.sourcesScroll}>
          <div
            className={styles.sourceGroupLabel}
            style={{ color: 'var(--blue)', background: 'var(--blue-tint)' }}
          >
            Citations
          </div>
          {citations.map((c, i) => (
            <div key={i} className={styles.sourceCard}>
              <div className={styles.sourceName}>{c.title}</div>
              {c.url && (
                <a
                  href={c.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.citationUrl}
                >
                  View source ↗
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [turns, setTurns] = useState<Turn[]>([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [latestCitations, setLatestCitations] = useState<LegalCitation[]>([])
  const [sourcesLoading, setSourcesLoading] = useState(false)
  const [hasLatestResponse, setHasLatestResponse] = useState(false)
  const messagesRef = useRef<HTMLDivElement>(null)
  /** Synchronous session id — avoids duplicate creates before React state commits. */
  const activeSessionIdRef = useRef<string | null>(null)
  const sessionTitleRef = useRef<string | null>(null)
  /** Skip one hydrate when we just created the session in submit (URL sync). */
  const skipSessionHydrateRef = useRef(false)

  const clearConversationState = useCallback(() => {
    setTurns([])
    setDraft('')
    setLatestCitations([])
    setSourcesLoading(false)
    setHasLatestResponse(false)
    activeSessionIdRef.current = null
    sessionTitleRef.current = null
  }, [])

  useEffect(() => {
    const sessionId = searchParams.get('session')
    if (!sessionId) {
      clearConversationState()
      return
    }
    if (skipSessionHydrateRef.current) {
      skipSessionHydrateRef.current = false
      activeSessionIdRef.current = sessionId
      return
    }
    const session = getSession(sessionId)
    if (!session) {
      clearConversationState()
      return
    }
    const loadedTurns: Turn[] = session.turns.map((turn) => {
      if (turn.role === 'user') return { id: nextId(), role: 'user' as const, text: turn.text }
      if ('response' in turn) {
        return { id: nextId(), role: 'assistant' as const, response: turn.response } as const
      }
      return { id: nextId(), role: 'assistant' as const, error: turn.error } as const
    })
    const sourceState = hydrateSources(loadedTurns)
    setTurns(loadedTurns)
    activeSessionIdRef.current = session.id
    sessionTitleRef.current = session.title
    setLatestCitations(sourceState.citations)
    setHasLatestResponse(sourceState.hasResponse)
    setSourcesLoading(false)
  }, [clearConversationState, searchParams])

  const scrollToBottom = useCallback(() => {
    // Double rAF ensures React has flushed and the DOM is painted before scrolling.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (messagesRef.current) {
          messagesRef.current.scrollTop = messagesRef.current.scrollHeight
        }
      })
    })
  }, [])

  const submit = useCallback(
    async (
      message: string,
      category?: string | null,
      displayText?: string,
      priorTurns?: Turn[],
    ) => {
      const text = message.trim()
      if (!text || loading) return

      const baseTurns = priorTurns ?? turns
      const conversation = buildAskConversationPayload(baseTurns)

      // Clear stale sources immediately so the panel never shows data from a
      // previous answer while a new request is in flight.
      setLatestCitations([])
      setSourcesLoading(true)

      const userLabel = displayText?.trim() || text
      const userTurn: Turn = { id: nextId(), role: 'user', text: userLabel }
      const pendingId = nextId()
      const optimisticTurns: Turn[] = [
        ...baseTurns,
        userTurn,
        { id: pendingId, role: 'assistant', pending: true },
      ]
      setTurns(optimisticTurns)

      const resolveSessionId = (): string => {
        if (activeSessionIdRef.current) return activeSessionIdRef.current
        const fromUrl = searchParams.get('session')
        if (fromUrl) {
          activeSessionIdRef.current = fromUrl
          return fromUrl
        }
        const newId = nextSessionId()
        activeSessionIdRef.current = newId
        sessionTitleRef.current = buildSessionTitle(text)
        skipSessionHydrateRef.current = true
        const params = new URLSearchParams(searchParams)
        params.set('session', newId)
        setSearchParams(params, { replace: true })
        return newId
      }

      const sessionId = resolveSessionId()

      const persistTurns = (nextTurns: Turn[]) => {
        const existing = getSession(sessionId)
        const title =
          sessionTitleRef.current ?? existing?.title ?? buildSessionTitle(text)
        if (!sessionTitleRef.current) sessionTitleRef.current = title
        saveSession({
          id: sessionId,
          title,
          updatedAt: Date.now(),
          turns: toStoredTurns(nextTurns),
        })
      }

      persistTurns(optimisticTurns)
      setLoading(true)
      scrollToBottom()

      try {
        const chatReq = {
          message: text,
          top_k: 5,
          selected_category: category ?? null,
          ...(conversation.length > 0 ? { conversation } : {}),
        }

        const response = await sendChatMessage(chatReq)
        setHasLatestResponse(true)
        setLatestCitations(response.citations)
        const nextTurns: Turn[] = optimisticTurns.map((t) =>
          t.id === pendingId ? { id: pendingId, role: 'assistant' as const, response } : t,
        )
        setTurns(nextTurns)
        persistTurns(nextTurns)
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'An unexpected error occurred.'
        const nextTurns: Turn[] = optimisticTurns.map((t) =>
          t.id === pendingId ? { id: pendingId, role: 'assistant' as const, error: msg } : t,
        )
        setTurns(nextTurns)
        persistTurns(nextTurns)
      } finally {
        setLoading(false)
        setSourcesLoading(false)
        scrollToBottom()
      }
    },
    [loading, scrollToBottom, searchParams, setSearchParams, turns],
  )

  const handleSend = useCallback(() => {
    const text = draft.trim()
    if (!text) return
    setDraft('')
    void submit(text, null, undefined, turns)
  }, [draft, submit, turns])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  const handleNewConversation = useCallback(() => {
    setSearchParams({}, { replace: true })
    clearConversationState()
  }, [clearConversationState, setSearchParams])

  return (
    <DashboardLayout
      rightPanel={
        <SourcesPanel
          citations={latestCitations}
          loading={sourcesLoading}
          hasResponse={hasLatestResponse}
        />
      }
    >
      <div className={styles.chatPanel}>
        <div className={styles.chatHeader}>
          <div>
            <div className={styles.chatTitle}>Ask a question</div>
            <div className={styles.chatSubtitle}>{CHAT_HEADER_SUBTITLE}</div>
          </div>
          {turns.length > 0 && (
            <button
              className={styles.sendBtn}
              onClick={handleNewConversation}
              style={{ padding: '6px 14px', fontSize: 12 }}
            >
              New conversation
            </button>
          )}
        </div>

        <div className={styles.messages} ref={messagesRef}>
          {turns.length === 0 && (
            <div className={styles.emptyState}>
              <div className={styles.emptyIcon}>⚖</div>
              <h2 className={styles.emptyTitle}>{CHAT_EMPTY_TITLE}</h2>
              <p className={styles.emptySub}>{CHAT_EMPTY_BODY}</p>
              <p className={styles.emptyLegal}>{PRODUCT_LEGAL_LINE}</p>
              <div className={styles.suggestions}>
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    className={styles.suggestionCard}
                    onClick={() => void submit(q)}
                    disabled={loading}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {turns.map((turn) => {
            if (turn.role === 'user') {
              return (
                <div key={turn.id} className={`${styles.messageBubble} ${styles.user}`}>
                  <div className={styles.roleLabel}>You</div>
                  <div className={styles.bubble}>{turn.text}</div>
                </div>
              )
            }
            if ('pending' in turn) {
              return (
                <div key={turn.id} className={`${styles.messageBubble} ${styles.assistant}`}>
                  <div className={styles.roleLabel}>Assistant</div>
                  <div className={styles.bubble} style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                    Reviewing official sources…
                  </div>
                </div>
              )
            }
            if ('error' in turn) {
              return (
                <div key={turn.id} className={`${styles.messageBubble} ${styles.assistant}`}>
                  <div className={styles.roleLabel}>Assistant</div>
                  <div
                    className={styles.bubble}
                    style={{ background: 'var(--error-tint)', borderColor: 'var(--error)', color: 'var(--error)' }}
                  >
                    {turn.error}
                  </div>
                </div>
              )
            }
            const { response } = turn
            return (
              <div key={turn.id} className={`${styles.messageBubble} ${styles.assistant}`}>
                <div className={styles.roleLabel}>Assistant</div>
                <div className={styles.bubble} style={{ width: '100%' }}>
                  <StructuredResultCard result={response} />
                </div>
              </div>
            )
          })}
        </div>

        <div className={styles.inputArea}>
          <div className={styles.inputRow}>
            <textarea
              className={styles.inputBox}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about EAD, asylum, green card, naturalization…"
              rows={1}
              disabled={loading}
            />
            <button
              className={styles.sendBtn}
              onClick={handleSend}
              disabled={loading || !draft.trim()}
            >
              Send
            </button>
          </div>
          <div className={styles.inputHint}>Press Enter to send · Shift+Enter for new line</div>
        </div>

        <div className={styles.disclaimerBar}>
          <span className={styles.disclaimerMoat}>{PRODUCT_MOAT_LINE}</span>
          <span className={styles.disclaimerLegal}>{PRODUCT_LEGAL_LINE}</span>
        </div>
      </div>
    </DashboardLayout>
  )
}
