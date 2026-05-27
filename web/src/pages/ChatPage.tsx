import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import DashboardLayout from '../components/layout/DashboardLayout'
import {
  buildAskConversationPayload,
  hasStructuredSections,
  parseFormattedAnswer,
  sendChatMessagePreferStream,
} from '../lib/api'
import type { ChatCitation, ChatUsedChunk, ClarificationOption, ChatResponse } from '../lib/api'
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
  | { id: number; role: 'assistant'; streaming: { text: string } }
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
  if (!assistantWithResponse || assistantWithResponse.response.status !== 'ok') {
    return { citations: [] as ChatCitation[], chunks: [] as ChatUsedChunk[], hasResponse: false }
  }
  return {
    citations: assistantWithResponse.response.citations,
    chunks: assistantWithResponse.response.used_chunks,
    hasResponse: true,
  }
}

function citationTitle(c: ChatCitation): string {
  if (c.topic?.trim()) {
    return c.subtopic?.trim() ? `${c.topic} — ${c.subtopic}` : c.topic
  }
  return c.citation
}

function ChatSourceDetails({
  privacyMode,
  activeDataset,
}: {
  privacyMode: string
  activeDataset?: string | null
}) {
  const [open, setOpen] = useState(false)
  if (!privacyMode && !activeDataset) return null
  return (
    <div style={{ marginBottom: 8 }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{
          border: 'none',
          background: 'transparent',
          color: 'var(--bronze)',
          fontSize: 12,
          fontWeight: 600,
          cursor: 'pointer',
          padding: '4px 0',
        }}
      >
        {open ? '▲' : '▼'} Source details
      </button>
      {open ? (
        <div style={{ fontSize: 10, color: 'var(--text-muted)', paddingLeft: 8, lineHeight: 1.4 }}>
          <div>Privacy: {privacyMode}</div>
          {activeDataset ? <div>Datasets: {activeDataset}</div> : null}
        </div>
      ) : null}
    </div>
  )
}

function AssistantAnswerBody({ response }: { response: ChatResponse }) {
  const [citationsOpen, setCitationsOpen] = useState(false)
  const sections = hasStructuredSections(response.answer)
    ? parseFormattedAnswer(response.answer)
    : [{ title: 'Information', body: response.answer }]
  const citationsMissing = response.citations.length === 0

  return (
    <>
      <ChatSourceDetails
        privacyMode={response.privacy_mode}
        activeDataset={response.active_dataset}
      />

      {sections.map((section, index) => {
        const isLead = section.title === 'Short answer'
        const isCaution = section.title === 'Important caution'
        if (isLead) {
          return (
            <p key={`${section.title}-${index}`} style={{ fontSize: 15, lineHeight: 1.55, margin: '0 0 10px' }}>
              {section.body}
            </p>
          )
        }
        return (
          <div key={`${section.title}-${index}`} style={{ marginBottom: 10 }}>
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                color: isCaution ? 'var(--navy)' : 'var(--bronze)',
                marginBottom: 4,
              }}
            >
              {section.title}
            </div>
            <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.55 }}>{section.body}</p>
          </div>
        )
      })}

      {response.mvp_sources.length > 0 ? (
        <div className={styles.answerMeta}>Searched: {response.mvp_sources.join(' · ')}</div>
      ) : null}

      {response.citations.length > 0 ? (
        <div style={{ marginTop: 10 }}>
          <button
            type="button"
            onClick={() => setCitationsOpen((v) => !v)}
            style={{
              border: 'none',
              background: 'transparent',
              color: 'var(--bronze)',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              padding: '4px 0',
            }}
          >
            {citationsOpen ? '▲' : '▼'} Official source links ({response.citations.length})
          </button>
          {citationsOpen
            ? response.citations.map((c, i) => (
                <div
                  key={`${c.citation}-${i}`}
                  style={{
                    marginTop: 8,
                    padding: '8px 10px',
                    background: 'var(--bg)',
                    border: '1px solid var(--border)',
                    borderLeft: '3px solid var(--bronze)',
                    borderRadius: 8,
                  }}
                >
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{citationTitle(c)}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                    {[c.citation, c.risk_level].filter(Boolean).join(' · ')}
                  </div>
                  {c.official_url ? (
                    <a
                      href={c.official_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className={styles.citationUrl}
                    >
                      View source ↗
                    </a>
                  ) : (
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      Official link not available
                    </span>
                  )}
                </div>
              ))
            : null}
        </div>
      ) : citationsMissing ? (
        <p style={{ fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic', marginTop: 8 }}>
          No official citations were returned for this answer. Verify details using primary government
          sources or a qualified immigration attorney.
        </p>
      ) : null}

      <div className={styles.answerFooter}>
        <p className={styles.answerMoat}>{PRODUCT_MOAT_LINE}</p>
        <p className={styles.answerLegal}>
          {response.disclaimer || PRODUCT_LEGAL_LINE}
        </p>
      </div>
    </>
  )
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
  citations: ChatCitation[]
  chunks: ChatUsedChunk[]
  loading: boolean
  hasResponse: boolean
}

function SourcesPanel({ citations, chunks, loading, hasResponse }: SourcesPanelProps) {
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
              <div className={styles.sourceName}>{c.citation}</div>
              {(c.topic || c.subtopic) && (
                <div className={styles.sourceDesc}>
                  {[c.topic, c.subtopic].filter(Boolean).join(' › ')}
                </div>
              )}
              {c.official_url && (
                <a
                  href={c.official_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.citationUrl}
                >
                  View source ↗
                </a>
              )}
            </div>
          ))}
          {chunks.length > 0 && (
            <>
              <div
                className={styles.sourceGroupLabel}
                style={{ color: 'var(--bronze)', background: 'var(--bronze-tint)', marginTop: 8 }}
              >
                Retrieved passages
              </div>
              {chunks.map((ch) => (
                <div key={ch.chunk_id} className={styles.sourceCard}>
                  <div className={styles.sourceName}>{ch.citation}</div>
                  <div className={styles.chunkSnippet}>{ch.snippet}</div>
                  {ch.source_family && (
                    <div className={styles.sourceDesc}>{ch.source_family}</div>
                  )}
                </div>
              ))}
            </>
          )}
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
  const [latestCitations, setLatestCitations] = useState<ChatCitation[]>([])
  const [latestChunks, setLatestChunks] = useState<ChatUsedChunk[]>([])
  const [sourcesLoading, setSourcesLoading] = useState(false)
  const [hasLatestResponse, setHasLatestResponse] = useState(false)
  const [pendingCategory, setPendingCategory] = useState<{ original: string } | null>(null)
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
    setLatestChunks([])
    setSourcesLoading(false)
    setHasLatestResponse(false)
    setPendingCategory(null)
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
    setLatestChunks(sourceState.chunks)
    setHasLatestResponse(sourceState.hasResponse)
    setSourcesLoading(false)
    setPendingCategory(null)
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
      setLatestChunks([])
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

        const response = await sendChatMessagePreferStream(chatReq, (accumulated) => {
          setTurns((prev) =>
            prev.map((t) => {
              if (t.id !== pendingId || t.role !== 'assistant') return t
              if ('pending' in t || 'streaming' in t) {
                return { id: pendingId, role: 'assistant' as const, streaming: { text: accumulated } }
              }
              return t
            }),
          )
        })

        if (response.status === 'needs_clarification') {
          // Clarification responses have no usable citations — leave panel empty.
          setPendingCategory({ original: text })
          const nextTurns: Turn[] = optimisticTurns.map((t) =>
            t.id === pendingId ? { id: pendingId, role: 'assistant' as const, response } : t,
          )
          setTurns(nextTurns)
          persistTurns(nextTurns)
        } else {
          setPendingCategory(null)
          setHasLatestResponse(true)
          setLatestCitations(response.citations)
          setLatestChunks(response.used_chunks)
          const nextTurns: Turn[] = optimisticTurns.map((t) =>
            t.id === pendingId ? { id: pendingId, role: 'assistant' as const, response } : t,
          )
          setTurns(nextTurns)
          persistTurns(nextTurns)
        }
      } catch (err) {
        setPendingCategory(null)
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

  const handleClarificationSelect = useCallback(
    (option: ClarificationOption) => {
      if (!pendingCategory || loading) return
      const { original } = pendingCategory
      setPendingCategory(null)
      void submit(original, option.value, option.label, turns)
    },
    [pendingCategory, loading, submit, turns],
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
          chunks={latestChunks}
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
            if ('streaming' in turn) {
              return (
                <div key={turn.id} className={`${styles.messageBubble} ${styles.assistant}`}>
                  <div className={styles.roleLabel}>Assistant</div>
                  <div className={styles.bubble}>
                    <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.55 }}>
                      {turn.streaming.text || ' '}
                    </p>
                    <p style={{ margin: '8px 0 0', fontSize: 12, color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      Reading official sources…
                    </p>
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
            if (response.status === 'needs_clarification') {
              return (
                <div key={turn.id} className={`${styles.messageBubble} ${styles.assistant}`}>
                  <div className={styles.roleLabel}>
                    Assistant
                    <span className={styles.privacyBadge}>{response.privacy_mode}</span>
                  </div>
                  <div className={styles.bubble}>
                    <p style={{ marginBottom: 10 }}>{response.answer}</p>
                    <p style={{ marginBottom: 12, color: 'var(--text-secondary)', fontSize: 13 }}>
                      {response.clarifying_question}
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                      {response.options.map((opt) => (
                        <button
                          key={opt.value}
                          onClick={() => handleClarificationSelect(opt)}
                          disabled={loading || !pendingCategory}
                          style={{
                            background: 'var(--blue-tint)',
                            color: 'var(--blue)',
                            border: '1px solid rgba(59,110,165,0.3)',
                            borderRadius: 99,
                            padding: '6px 14px',
                            fontSize: 12.5,
                            fontWeight: 500,
                            cursor: 'pointer',
                            opacity: loading || !pendingCategory ? 0.5 : 1,
                          }}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )
            }
            return (
              <div key={turn.id} className={`${styles.messageBubble} ${styles.assistant}`}>
                <div className={styles.roleLabel}>
                  Assistant
                  <span className={styles.privacyBadge}>{response.privacy_mode}</span>
                </div>
                <div className={styles.bubble}>
                  <AssistantAnswerBody response={response} />
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
