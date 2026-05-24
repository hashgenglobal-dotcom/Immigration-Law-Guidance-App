import { useCallback, useRef, useState } from 'react'
import DashboardLayout from '../components/layout/DashboardLayout'
import { sendChatMessage } from '../lib/api'
import type { ChatMessage, ClarificationOption, ChatResponse } from '../lib/api'
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
    color: '#a07830',
    colorTint: '#faf4e8',
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

function SourcesPanel({ citations }: { citations: string[] }) {
  const hasCitations = citations.length > 0

  return (
    <div className={styles.sourcesPanel}>
      <div className={styles.sourcesHeader}>
        Source Preview
        {hasCitations && (
          <span style={{ fontWeight: 400, color: 'var(--text-secondary)', fontSize: 12, marginLeft: 8 }}>
            {citations.length} cited
          </span>
        )}
      </div>

      {!hasCitations && (
        <p className={styles.sourcesExplainer}>
          Cited regulations, forms, policy sections, and decisions appear here when answers are generated.
        </p>
      )}

      <div className={styles.sourcesScroll}>
        {hasCitations ? (
          citations.map((c, i) => (
            <div key={i} className={styles.sourceCard}>
              <div className={styles.sourceType}>Citation</div>
              <div className={styles.sourceName}>{c}</div>
            </div>
          ))
        ) : (
          SAMPLE_SOURCE_GROUPS.map((group) => (
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
          ))
        )}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const [turns, setTurns] = useState<Turn[]>([])
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [latestCitations, setLatestCitations] = useState<string[]>([])
  const [pendingCategory, setPendingCategory] = useState<{ original: string } | null>(null)
  const messagesRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      if (messagesRef.current) {
        messagesRef.current.scrollTop = messagesRef.current.scrollHeight
      }
    })
  }, [])

  const buildConversation = useCallback((): ChatMessage[] => {
    const messages: ChatMessage[] = []
    for (const t of turns) {
      if (t.role === 'user') {
        messages.push({ role: 'user', content: t.text })
      } else if ('response' in t && t.response.status === 'ok') {
        messages.push({ role: 'assistant', content: t.response.answer })
      }
    }
    return messages
  }, [turns])

  const submit = useCallback(
    async (message: string, category?: string | null, displayText?: string) => {
      const text = message.trim()
      if (!text || loading) return

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
        const conversation = buildConversation()
        const response = await sendChatMessage({
          message: text,
          top_k: 5,
          selected_category: category ?? null,
          conversation,
        })

        if (response.status === 'needs_clarification') {
          setPendingCategory({ original: text })
          setTurns((prev) =>
            prev.map((t) =>
              t.id === pendingId ? { id: pendingId, role: 'assistant', response } : t,
            ),
          )
        } else {
          setPendingCategory(null)
          setLatestCitations(response.citations)
          setTurns((prev) =>
            prev.map((t) =>
              t.id === pendingId ? { id: pendingId, role: 'assistant', response } : t,
            ),
          )
        }
      } catch {
        setPendingCategory(null)
        setTurns((prev) =>
          prev.map((t) =>
            t.id === pendingId
              ? { id: pendingId, role: 'assistant', error: 'Could not reach the backend. Make sure it is running on port 8000.' }
              : t,
          ),
        )
      } finally {
        setLoading(false)
        scrollToBottom()
      }
    },
    [loading, scrollToBottom, buildConversation],
  )

  const handleSend = useCallback(() => {
    const text = draft.trim()
    if (!text) return
    setDraft('')
    void submit(text)
  }, [draft, submit])

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
      void submit(original, option.value, option.label)
    },
    [pendingCategory, loading, submit],
  )

  const handleNewConversation = useCallback(() => {
    setTurns([])
    setDraft('')
    setLatestCitations([])
    setPendingCategory(null)
  }, [])

  return (
    <DashboardLayout rightPanel={<SourcesPanel citations={latestCitations} />}>
      <div className={styles.chatPanel}>
        <div className={styles.chatHeader}>
          <div>
            <div className={styles.chatTitle}>Ask a question</div>
            <div className={styles.chatSubtitle}>
              Official-source grounded answers to U.S. immigration questions
            </div>
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
              <h2 className={styles.emptyTitle}>Ask an immigration question</h2>
              <p className={styles.emptySub}>
                Answers are grounded in official federal regulations, USCIS policy, and court rules.
                Sources are cited inline with every response.
              </p>
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
                  <div className={styles.roleLabel}>Assistant</div>
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
                <div className={styles.roleLabel}>Assistant</div>
                <div className={styles.bubble}>
                  <p style={{ whiteSpace: 'pre-wrap' }}>{response.answer}</p>
                  {response.citations.length > 0 && (
                    <div className={styles.citationRow}>
                      {response.citations.map((c) => (
                        <span key={c} className={styles.citationChip}>{c}</span>
                      ))}
                    </div>
                  )}
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
          This app provides legal information and guidance, not legal advice. For personal legal
          decisions, consult a qualified immigration attorney.
        </div>
      </div>
    </DashboardLayout>
  )
}
