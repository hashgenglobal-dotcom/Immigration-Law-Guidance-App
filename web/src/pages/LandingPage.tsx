import { Link } from 'react-router-dom'
import styles from './LandingPage.module.css'

const FEATURES = [
  {
    icon: '◈',
    title: 'Official source-grounded answers',
    desc: 'Every answer draws from CFR sections, USCIS policy manual, immigration court rules, and INA statutes.',
  },
  {
    icon: '◉',
    title: 'Multi-turn conversation context',
    desc: 'Follow-up questions are understood in context. Ask about EAD, then ask a follow-up — it stays coherent.',
  },
  {
    icon: '◎',
    title: 'Immigration update feed',
    desc: 'Curated USCIS policy updates, Federal Register notices, and BIA decisions. Coming in Milestone 2.',
  },
  {
    icon: '○',
    title: 'Full citation transparency',
    desc: 'See exactly which regulations or forms were cited. Citations appear inline with every answer.',
  },
]

const MOCK_CHAT = [
  {
    role: 'user' as const,
    text: 'How do I apply for an EAD as an asylum applicant?',
  },
  {
    role: 'assistant' as const,
    text: 'Asylum applicants may file Form I-765 after 150 days from submitting a complete asylum application. You must include a copy of your asylum filing receipt.',
    citation: '8 CFR § 208.7 · Form I-765',
  },
]

export default function LandingPage() {
  return (
    <div className={styles.page}>
      {/* Top navigation */}
      <header className={styles.topnav}>
        <div className={styles.topnavInner}>
          <div className={styles.brand}>
            <span className={styles.brandIcon}>⚖</span>
            <span className={styles.brandName}>Immigration Law Guidance</span>
          </div>
          <nav className={styles.topnavLinks}>
            <Link to="/chat" className={styles.topnavLink}>Chat</Link>
            <Link to="/updates" className={styles.topnavLink}>Updates</Link>
            <Link to="/sources" className={styles.topnavLink}>Sources</Link>
            <Link to="/about" className={styles.topnavLink}>About</Link>
            <Link to="/chat" className={styles.topnavCta}>Open Chat →</Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className={styles.hero}>
        <div className={styles.heroInner}>
          <div className={styles.heroLeft}>
            <div className={styles.heroBadge}>Informational Tool · MVP</div>
            <h1 className={styles.heroTitle}>
              U.S. Immigration<br />Law Guidance
            </h1>
            <p className={styles.heroSub}>
              Ask questions about U.S. immigration processes and get answers grounded in official
              federal regulations, USCIS policy, and immigration court rules. Sources are cited inline
              with every answer.
            </p>
            <div className={styles.heroCtas}>
              <Link to="/chat" className={styles.ctaPrimary}>Open Chat</Link>
              <Link to="/sources" className={styles.ctaSecondary}>View Sources</Link>
            </div>
            <div className={styles.heroStats}>
              <span className={styles.heroStat}><strong>15+</strong> official sources</span>
              <span className={styles.heroStatDivider}>·</span>
              <span className={styles.heroStat}><strong>EAD, asylum, AOS</strong> and more</span>
              <span className={styles.heroStatDivider}>·</span>
              <span className={styles.heroStat}><strong>Session-based context</strong></span>
            </div>
          </div>

          <div className={styles.heroRight}>
            <div className={styles.mockChat}>
              <div className={styles.mockChatHeader}>
                <span>Ask a question</span>
                <span className={styles.mockLive}>● Live</span>
              </div>
              {MOCK_CHAT.map((m, i) => (
                <div key={i} className={m.role === 'user' ? styles.mockUser : styles.mockAssistant}>
                  <div className={styles.mockLabel}>{m.role === 'user' ? 'You' : 'Assistant'}</div>
                  <div className={styles.mockBubble}>{m.text}</div>
                  {m.citation && (
                    <div className={styles.mockCitationRow}>
                      <span className={styles.mockCitationChip}>{m.citation}</span>
                    </div>
                  )}
                </div>
              ))}
              <div className={styles.mockInput}>
                <span className={styles.mockInputText}>Ask about EAD, asylum, green card…</span>
                <span className={styles.mockSendBtn}>Send</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className={styles.features}>
        <div className={styles.featuresInner}>
          <h2 className={styles.featuresTitle}>Built for legal clarity</h2>
          <div className={styles.featuresGrid}>
            {FEATURES.map((f) => (
              <div key={f.title} className={styles.featureCard}>
                <div className={styles.featureIcon}>{f.icon}</div>
                <div className={styles.featureTitle}>{f.title}</div>
                <div className={styles.featureDesc}>{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Legal disclaimer */}
      <section className={styles.disclaimerSection}>
        <div className={styles.disclaimerInner}>
          <strong>Legal disclaimer:</strong> This app provides legal information and guidance, not legal
          advice. For personal legal decisions — including asylum applications, removal proceedings, visa
          petitions, or naturalization — consult a qualified immigration attorney.
        </div>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerInner}>
          <span>Immigration Law Guidance · Web MVP</span>
          <span>Informational tool — not legal advice</span>
        </div>
      </footer>
    </div>
  )
}
