import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { brand } from '../../lib/brand'
import {
  CHAT_HISTORY_UPDATED_EVENT,
  deleteSession,
  getSessions,
  type ChatSession,
} from '../../lib/chatHistory'
import styles from './Sidebar.module.css'

const NAV_ITEMS = [
  { label: 'Home', to: '/', icon: '⌂', end: true },
  { label: 'Ask a question', to: '/chat', icon: '💬', end: false },
  { label: 'Browse scenarios', to: '/scenarios', icon: '📚', end: false },
  { label: 'Official Updates', to: '/updates', icon: '📰', end: false },
  { label: 'Sources', to: '/sources', icon: '🔗', end: false },
  { label: 'About', to: '/about', icon: '○', end: false },
] as const

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()
  const [sessions, setSessions] = useState<ChatSession[]>([])

  const loadSessions = useCallback(() => {
    setSessions(getSessions())
  }, [])

  useEffect(() => {
    loadSessions()
    const onStorage = () => loadSessions()
    const onUpdated = () => loadSessions()
    window.addEventListener('storage', onStorage)
    window.addEventListener(CHAT_HISTORY_UPDATED_EVENT, onUpdated)
    return () => {
      window.removeEventListener('storage', onStorage)
      window.removeEventListener(CHAT_HISTORY_UPDATED_EVENT, onUpdated)
    }
  }, [loadSessions])

  const activeSessionId = useMemo(() => {
    const params = new URLSearchParams(location.search)
    return params.get('session')
  }, [location.search])

  const handleDelete = useCallback(
    (sessionId: string) => {
      deleteSession(sessionId)
      if (activeSessionId === sessionId) navigate('/chat')
      else loadSessions()
    },
    [activeSessionId, loadSessions, navigate],
  )

  return (
    <aside className={styles.sidebar}>
      <Link to="/" className={styles.brandLink}>
        <div className={styles.brandRow}>
          <img src="/sourcepath-icon.png" alt="" className={styles.brandLogo} width={28} height={28} />
          <span className={styles.brandName}>{brand.name}</span>
        </div>
        <div className={styles.brandSub}>{brand.tagline}</div>
      </Link>

      <nav className={styles.nav}>
        <div className={styles.navLabel}>Navigation</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.active}` : styles.navLink
            }
          >
            <span className={styles.navIcon}>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className={styles.history}>
        <div className={styles.historyLabel}>Recent conversations</div>
        {sessions.map((session) => (
          <div
            key={session.id}
            className={styles.historyItem}
            title={session.title}
            role="button"
            tabIndex={0}
            onClick={() => navigate(`/chat?session=${encodeURIComponent(session.id)}`)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') navigate(`/chat?session=${encodeURIComponent(session.id)}`)
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              color: activeSessionId === session.id ? '#ffffff' : undefined,
              background: activeSessionId === session.id ? 'rgba(255, 255, 255, 0.08)' : undefined,
            }}
          >
            <span
              style={{
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                paddingRight: 8,
              }}
            >
              {session.title}
            </span>
            <button
              type="button"
              aria-label={`Delete conversation ${session.title}`}
              onClick={(e) => {
                e.stopPropagation()
                handleDelete(session.id)
              }}
              style={{
                border: 'none',
                background: 'transparent',
                color: 'rgba(255, 255, 255, 0.55)',
                cursor: 'pointer',
                fontSize: 13,
                padding: '0 0 0 6px',
              }}
            >
              ×
            </button>
          </div>
        ))}
        <button type="button" className={styles.newChatBtn} onClick={() => navigate('/chat')}>
          + New conversation
        </button>
      </div>

      <div className={styles.disclaimer}>
        {brand.motto} · verifiable sources, not legal advice
      </div>
    </aside>
  )
}
