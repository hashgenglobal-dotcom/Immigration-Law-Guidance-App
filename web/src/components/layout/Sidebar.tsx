import { Link, NavLink, useNavigate } from 'react-router-dom'
<<<<<<< HEAD
=======
import { brand } from '../../lib/brand'
>>>>>>> features/more-guide
import styles from './Sidebar.module.css'

const NAV_ITEMS = [
  { label: 'Home', to: '/', icon: '⌂', end: true },
<<<<<<< HEAD
  { label: 'Chat', to: '/chat', icon: '◈', end: false },
  { label: 'Official Updates', to: '/updates', icon: '◉', end: false },
  { label: 'Sources', to: '/sources', icon: '◎', end: false },
=======
  { label: 'Ask a question', to: '/chat', icon: '💬', end: false },
  { label: 'Browse scenarios', to: '/scenarios', icon: '📚', end: false },
  { label: 'Official Updates', to: '/updates', icon: '📰', end: false },
  { label: 'Sources', to: '/sources', icon: '🔗', end: false },
>>>>>>> features/more-guide
  { label: 'About', to: '/about', icon: '○', end: false },
] as const

const PLACEHOLDER_HISTORY = [
<<<<<<< HEAD
  'EAD application process',
  'Asylum eligibility requirements',
  'Green card adjustment of status',
  'F-1 OPT STEM extension',
=======
  'F-1 status basics',
  'Post-completion OPT',
  'H-1B cap registration',
  'Adjustment of status',
>>>>>>> features/more-guide
]

export default function Sidebar() {
  const navigate = useNavigate()

  return (
    <aside className={styles.sidebar}>
      <Link to="/" className={styles.brandLink}>
        <div className={styles.brandRow}>
<<<<<<< HEAD
          <span className={styles.brandIcon}>⚖</span>
          <span className={styles.brandName}>Immigration Law</span>
        </div>
        <div className={styles.brandSub}>Guidance Tool</div>
=======
          <img src="/sourcepath-icon.png" alt="" className={styles.brandLogo} width={28} height={28} />
          <span className={styles.brandName}>{brand.name}</span>
        </div>
        <div className={styles.brandSub}>{brand.tagline}</div>
>>>>>>> features/more-guide
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
<<<<<<< HEAD
=======
            onKeyDown={(e) => e.key === 'Enter' && navigate('/chat')}
            role="button"
            tabIndex={0}
>>>>>>> features/more-guide
          >
            {label}
          </div>
        ))}
<<<<<<< HEAD
        <button className={styles.newChatBtn} onClick={() => navigate('/chat')}>
=======
        <button type="button" className={styles.newChatBtn} onClick={() => navigate('/chat')}>
>>>>>>> features/more-guide
          + New conversation
        </button>
      </div>

      <div className={styles.disclaimer}>
<<<<<<< HEAD
        Legal information only — not legal advice. Consult a qualified attorney for personal decisions.
=======
        {brand.motto} · verifiable sources, not legal advice
>>>>>>> features/more-guide
      </div>
    </aside>
  )
}
