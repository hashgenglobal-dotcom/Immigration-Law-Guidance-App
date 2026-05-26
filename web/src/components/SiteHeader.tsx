import { Link, NavLink } from 'react-router-dom'
import { brand } from '../lib/brand'
import styles from './SiteHeader.module.css'

const NAV = [
  { to: '/chat', label: 'Ask a question' },
  { to: '/scenarios', label: 'Scenario' },
  { to: '/updates', label: 'Updates' },
  { to: '/sources', label: 'Sources' },
  { to: '/about', label: 'About' },
] as const

export default function SiteHeader({ showCta = true }: { showCta?: boolean }) {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link to="/" className={styles.brand}>
          <img src="/sourcepath-icon.png" alt="" className={styles.logo} width={32} height={32} />
          <span className={styles.brandText}>
            <span className={styles.brandName}>{brand.name}</span>
            <span className={styles.brandTagline}>{brand.tagline}</span>
          </span>
        </Link>
        <nav className={styles.nav} aria-label="Main">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
              }
            >
              {item.label}
            </NavLink>
          ))}
          {showCta ? (
            <Link to="/chat" className={styles.cta}>
              Open Chat →
            </Link>
          ) : null}
        </nav>
      </div>
    </header>
  )
}
