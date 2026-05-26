import { Link } from 'react-router-dom'
import DigitalBackdrop from '../components/DigitalBackdrop'
import DisclaimerAccordion from '../components/DisclaimerAccordion'
import SiteHeader from '../components/SiteHeader'
import { brand } from '../lib/brand'
import { scenarioGuides } from '../lib/scenarioGuides'
import styles from './LandingPage.module.css'

const EXPLORE = [
  {
    id: 'ask',
    to: '/chat',
    icon: '💬',
    title: 'Ask a question',
    subtitle: 'Plain-language answers with citation-first retrieval.',
  },
  {
    id: 'scenarios',
    to: '/scenarios',
    icon: '📚',
    title: 'Browse scenarios',
    subtitle: '12 step-by-step guides for common situations.',
  },
  {
    id: 'updates',
    to: '/updates',
    icon: '📰',
    title: 'Official updates',
    subtitle: 'USCIS, Federal Register, and BIA highlights.',
  },
  {
    id: 'about',
    to: '/about',
    icon: '○',
    title: 'About SourcePath',
    subtitle: 'Principles, privacy, and how we cite sources.',
  },
] as const

const FEATURES = [
  {
    icon: '◈',
    title: 'Citation-first answers',
    desc: 'Responses draw from retrieved CFR, USCIS policy, INA, and agency guidance—not unchecked model memory.',
    to: '/chat',
    cta: 'Open Ask',
  },
  {
    icon: '◉',
    title: 'Conversation context',
    desc: 'Follow-up questions stay coherent within your session so you can drill into deadlines and eligibility.',
    to: '/chat',
    cta: 'Start chatting',
  },
  {
    icon: '◎',
    title: 'Official updates feed',
    desc: 'Curated USCIS policy changes, Federal Register notices, and BIA decisions (preview on web).',
    to: '/updates',
    cta: 'View updates',
  },
  {
    icon: '○',
    title: 'Scenario guides',
    desc: 'F-1, OPT, H-1B, adjustment of status, and more—with overview, key points, and source links.',
    to: '/scenarios',
    cta: 'Browse guides',
  },
] as const

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
] as const

const FEATURED_SCENARIOS = scenarioGuides.slice(0, 3)

export default function LandingPage() {
  return (
    <div className={styles.page}>
      <DigitalBackdrop />
      <SiteHeader />
      <div className={styles.pageContent}>
        {/* Hero — Vercel two-column + SourcePath copy */}
        <section className={styles.hero} aria-labelledby="hero-title">
          <div className={styles.heroInner}>
            <div className={styles.heroLeft}>
              <div className={styles.heroBadge}>
                <span className={styles.heroBadgeIcon} aria-hidden>
                  ⚖
                </span>
                {brand.motto}
              </div>
              <h1 id="hero-title" className={styles.heroTitle}>
                {brand.name}
              </h1>
              <p className={styles.heroTagline}>{brand.tagline}</p>
              <p className={styles.heroSub}>{brand.description}</p>
              <div className={styles.heroCtas}>
                <Link to="/chat" className={styles.ctaPrimary}>
                  Ask a question
                </Link>
                <Link to="/scenarios" className={styles.ctaSecondary}>
                  Browse scenarios
                </Link>
              </div>
              <div className={styles.heroStats}>
                <span className={styles.heroStat}>
                  <strong>12</strong> scenario guides
                </span>
                <span className={styles.heroStatDivider}>·</span>
                <span className={styles.heroStat}>
                  <strong>Official</strong> sources cited
                </span>
                <span className={styles.heroStatDivider}>·</span>
                <span className={styles.heroStat}>
                  <strong>{brand.motto}</strong>
                </span>
              </div>
            </div>

            <div className={styles.heroRight}>
              <Link to="/chat" className={styles.mockChatLink} aria-label="Open chat assistant">
                <div className={styles.mockChat}>
                  <div className={styles.mockChatHeader}>
                    <span>Ask a question</span>
                    <span className={styles.mockLive}>● Live</span>
                  </div>
                  {MOCK_CHAT.map((m, i) => (
                    <div key={i} className={m.role === 'user' ? styles.mockUser : styles.mockAssistant}>
                      <div className={styles.mockLabel}>{m.role === 'user' ? 'You' : 'Assistant'}</div>
                      <div className={styles.mockBubble}>{m.text}</div>
                      {'citation' in m && m.citation ? (
                        <div className={styles.mockCitationRow}>
                          <span className={styles.mockCitationChip}>{m.citation}</span>
                        </div>
                      ) : null}
                    </div>
                  ))}
                  <div className={styles.mockInput}>
                    <span className={styles.mockInputText}>Ask about EAD, asylum, green card…</span>
                    <span className={styles.mockSendBtn}>Send</span>
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </section>

        {/* Explore — mobile HomeExploreSection at desktop width */}
        <section className={styles.explore} aria-labelledby="explore-title">
          <div className={styles.exploreInner}>
            <div className={styles.exploreHeader}>
              <div className={styles.exploreAccent} aria-hidden />
              <div>
                <p className={styles.exploreEyebrow}>Explore</p>
                <h2 id="explore-title" className={styles.exploreTitle}>
                  Where would you like to go?
                </h2>
              </div>
            </div>
            <div className={styles.exploreGrid}>
              {EXPLORE.map((item) => (
                <Link key={item.id} to={item.to} className={styles.exploreTile}>
                  <span className={styles.tileAccent} aria-hidden />
                  <span className={styles.tileIcon}>{item.icon}</span>
                  <span className={styles.tileCopy}>
                    <span className={styles.tileTitle}>{item.title}</span>
                    <span className={styles.tileSubtitle}>{item.subtitle}</span>
                  </span>
                  <span className={styles.tileChevron} aria-hidden>
                    →
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Features — Vercel grid + mobile capabilities */}
        <section className={styles.features} aria-labelledby="features-title">
          <div className={styles.featuresInner}>
            <h2 id="features-title" className={styles.featuresTitle}>
              Built for legal clarity
            </h2>
            <p className={styles.featuresLead}>
              SourcePath combines the breadth of a web assistant with the focused experience you know from
              mobile—grounded answers, guides, and official-source transparency.
            </p>
            <div className={styles.featuresGrid}>
              {FEATURES.map((f) => (
                <Link key={f.title} to={f.to} className={styles.featureCard}>
                  <div className={styles.featureIcon}>{f.icon}</div>
                  <div className={styles.featureTitle}>{f.title}</div>
                  <div className={styles.featureDesc}>{f.desc}</div>
                  <span className={styles.featureCta}>{f.cta} →</span>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Featured scenarios from mobile library */}
        <section className={styles.scenariosPreview} aria-labelledby="scenarios-preview-title">
          <div className={styles.scenariosPreviewInner}>
            <div className={styles.scenariosPreviewHead}>
              <div>
                <p className={styles.exploreEyebrow}>Guides</p>
                <h2 id="scenarios-preview-title" className={styles.scenariosPreviewTitle}>
                  Popular scenario guides
                </h2>
              </div>
              <Link to="/scenarios" className={styles.viewAllLink}>
                View all 12 guides →
              </Link>
            </div>
            <div className={styles.scenariosPreviewGrid}>
              {FEATURED_SCENARIOS.map((s) => (
                <Link key={s.id} to={`/scenarios?s=${encodeURIComponent(s.id)}`} className={styles.scenarioCard}>
                  <div className={styles.scenarioCardTop}>
                    <h3 className={styles.scenarioCardTitle}>{s.title}</h3>
                    <span className={`${styles.risk} ${styles[`risk_${s.riskLevel}`]}`}>{s.riskLevel}</span>
                  </div>
                  <p className={styles.scenarioCardDesc}>{s.shortDescription}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.disclaimerWrap}>
          <div className={styles.disclaimerInner}>
            <DisclaimerAccordion />
          </div>
        </section>

        <footer className={styles.footer}>
          <div className={styles.footerInner}>
            <p className={styles.footerDisclaimer}>
              <strong>Legal disclaimer:</strong> This app provides general immigration information only, not
              legal advice. For urgent, high-risk, or case-specific situations, contact a qualified
              immigration attorney.
            </p>
            <div className={styles.footerMeta}>
              <span>
                {brand.name} · {brand.company}
              </span>
              <span>{brand.tagline}</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}
