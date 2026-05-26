import { useCallback, useRef, useState } from 'react'
import DashboardLayout from '../components/layout/DashboardLayout'
import { buildAskConversationPayload, sendChatMessage } from '../lib/api'
import type { ChatCitation, ChatUsedChunk, ClarificationOption, ChatResponse } from '../lib/api'
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
  const [turns, setTurns] = useState<Turn[]>([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [latestCitations, setLatestCitations] = useState<ChatCitation[]>([])
  const [latestChunks, setLatestChunks] = useState<ChatUsedChunk[]>([])
  const [sourcesLoading, setSourcesLoading] = useState(false)
  const [hasLatestResponse, setHasLatestResponse] = useState(false)
  const [pendingCategory, setPendingCategory] = useState<{ original: string } | null>(null)
  const messagesRef = useRef<HTMLDivElement>(null)

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

      const conversation = buildAskConversationPayload(priorTurns ?? turns)

      // Clear stale sources immediately so the panel never shows data from a
      // previous answer while a new request is in flight.
      setLatestCitations([])
      setLatestChunks([])
      setSourcesLoading(true)

      const userLabel = displayText?.trim() || text
      const userTurn: Turn = { id: nextId(), role: 'user', text: userLabel }
      const pendingId = nextId()

      setTurns((prev) => [
        ...prev,
        userTurn,
        { id: pendingId, role: 'assistant', pending: true },
      ])
      setLoading(true)
      scrollToBottom()

      try {
        const response = await sendChatMessage({
          message: text,
          top_k: 5,
          selected_category: category ?? null,
          ...(conversation.length > 0 ? { conversation } : {}),
        })

        if (response.status === 'needs_clarification') {
          // Clarification responses have no usable citations — leave panel empty.
          setPendingCategory({ original: text })
          setTurns((prev) =>
            prev.map((t) =>
              t.id === pendingId ? { id: pendingId, role: 'assistant', response } : t,
            ),
          )
        } else {
          setPendingCategory(null)
          setHasLatestResponse(true)
          setLatestCitations(response.citations)
          setLatestChunks(response.used_chunks)
          setTurns((prev) =>
            prev.map((t) =>
              t.id === pendingId ? { id: pendingId, role: 'assistant', response } : t,
            ),
          )
        }
      } catch (err) {
        setPendingCategory(null)
        const msg = err instanceof Error ? err.message : 'An unexpected error occurred.'
        setTurns((prev) =>
          prev.map((t) =>
            t.id === pendingId
              ? { id: pendingId, role: 'assistant', error: msg }
              : t,
          ),
        )
      } finally {
        setLoading(false)
        setSourcesLoading(false)
        scrollToBottom()
      }
    },
    [loading, scrollToBottom, turns],
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
    setTurns([])
    setDraft('')
    setLatestCitations([])
    setLatestChunks([])
    setSourcesLoading(false)
    setHasLatestResponse(false)
    setPendingCategory(null)
  }, [])

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
                  <p style={{ whiteSpace: 'pre-wrap' }}>{response.answer}</p>
                  {response.mvp_sources.length > 0 && (
                    <div className={styles.answerMeta}>
                      Searched: {response.mvp_sources.join(' · ')}
                    </div>
                  )}
                  {response.citations.length > 0 && (
                    <div className={styles.citationRow}>
                      {response.citations.map((c, i) => (
                        <span key={`${i}-${c.citation}`} className={styles.citationChip}>
                          {c.citation}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className={styles.answerFooter}>
                    <p className={styles.answerMoat}>{PRODUCT_MOAT_LINE}</p>
                    <p className={styles.answerLegal}>{PRODUCT_LEGAL_LINE}</p>
                  </div>
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
