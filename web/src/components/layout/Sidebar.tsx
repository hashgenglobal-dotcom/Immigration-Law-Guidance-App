import { Link, NavLink, useNavigate } from 'react-router-dom'
import styles from './Sidebar.module.css'

const NAV_ITEMS = [
  { label: 'Home', to: '/', icon: '⌂', end: true },
  { label: 'Chat', to: '/chat', icon: '◈', end: false },
  { label: 'Official Updates', to: '/updates', icon: '◉', end: false },
  { label: 'Sources', to: '/sources', icon: '◎', end: false },
  { label: 'About', to: '/about', icon: '○', end: false },
] as const

const PLACEHOLDER_HISTORY = [
  'EAD application process',
  'Asylum eligibility requirements',
  'Green card adjustment of status',
  'F-1 OPT STEM extension',
]

export default function Sidebar() {
  const navigate = useNavigate()

  return (
    <aside className={styles.sidebar}>
      <Link to="/" className={styles.brandLink}>
        <div className={styles.brandRow}>
          <span className={styles.brandIcon}>⚖</span>
          <span className={styles.brandName}>Immigration Law</span>
        </div>
        <div className={styles.brandSub}>Guidance Tool</div>
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
        {PLACEHOLDER_HISTORY.map((label) => (
          <div
            key={label}
            className={styles.historyItem}
            title={label}
            onClick={() => navigate('/chat')}
          >
            {label}
          </div>
        ))}
        <button className={styles.newChatBtn} onClick={() => navigate('/chat')}>
          + New conversation
        </button>
      </div>

      <div className={styles.disclaimer}>
        Legal information only — not legal advice. Consult a qualified attorney for personal decisions.
      </div>
    </aside>
  )
}
