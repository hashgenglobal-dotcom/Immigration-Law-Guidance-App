import { Link } from 'react-router-dom'
import DisclaimerAccordion from '../components/DisclaimerAccordion'
import DashboardLayout from '../components/layout/DashboardLayout'
import {
  ABOUT_MISSION,
  ABOUT_PRINCIPLES,
  EXPLORE_ACTIONS,
  TRUST_PILLARS,
} from '../lib/aboutContent'
import { brand } from '../lib/brand'
import { SOURCE_CATALOG, catalogStats, familyMeta } from '../lib/sourceCatalog'
import { ABOUT_NAVY_LEGAL_NOTICE_LABEL, LEGAL_DISCLAIMER_FULL } from '../lib/legalCopy'
import styles from './AboutPage.module.css'

export default function AboutPage() {
  const sourceStats = catalogStats()
  const previewSources = SOURCE_CATALOG.filter((s) => s.status === 'indexed').slice(0, 6)

  return (
    <DashboardLayout>
      <div className={styles.page}>
        {/* Wide navy hero — mission + identity (once) */}
        <header className={styles.navyBanner}>
          <div className={styles.navyBannerArt} aria-hidden />
          <div className={styles.navyBannerInner}>
            <div className={styles.mission}>
              <p className={styles.missionEyebrow}>{ABOUT_MISSION.eyebrow}</p>
              <h1 className={styles.missionHeadline}>{ABOUT_MISSION.headline}</h1>
              <p className={styles.missionLead}>{ABOUT_MISSION.lead}</p>
              <p className={styles.missionBody}>{ABOUT_MISSION.body}</p>
              <div className={styles.missionActions}>
                <Link to="/chat" className={styles.missionCtaPrimary}>
                  Ask a question
                </Link>
                <Link to="/sources#catalog" className={styles.missionCtaSecondary}>
                  Browse source library
                </Link>
              </div>
            </div>

            <aside className={styles.identity} aria-label="SourcePath">
              <div className={styles.identityBrand}>
                <img
                  src="/sourcepath-icon.png"
                  alt=""
                  className={styles.identityLogo}
                  width={52}
                  height={52}
                />
                <div>
                  <p className={styles.identityName}>{brand.name}</p>
                  <p className={styles.identityTagline}>{brand.tagline}</p>
                </div>
              </div>
              <p className={styles.identityMotto}>{brand.motto}</p>
              <p className={styles.identityCompany}>{brand.company}</p>

              <div className={styles.trustStrip} role="list" aria-label="How we work">
                {TRUST_PILLARS.map((p) => {
                  const inner = (
                    <>
                      <span className={styles.trustStripIcon} aria-hidden>
                        {p.icon}
                      </span>
                      <span className={styles.trustStripLabel}>{p.label}</span>
                      <span className={styles.trustStripHint}>{p.desc}</span>
                    </>
                  )
                  return 'linkTo' in p && p.linkTo ? (
                    <Link
                      key={p.label}
                      to={p.linkTo}
                      className={`${styles.trustStripTile} ${styles.trustStripTileLink}`}
                      role="listitem"
                    >
                      {inner}
                    </Link>
                  ) : (
                    <div key={p.label} className={styles.trustStripTile} role="listitem">
                      {inner}
                    </div>
                  )
                })}
              </div>
            </aside>
          </div>

          <div className={styles.navyDisclaimer} role="note" aria-labelledby="navy-legal-notice">
            <p id="navy-legal-notice" className={styles.navyDisclaimerLabel}>
              {ABOUT_NAVY_LEGAL_NOTICE_LABEL}
            </p>
            <p className={styles.navyDisclaimerText}>
              We are <span className={styles.navyDisclaimerHighlight}>NOT A LAWYER</span> and{' '}
              <span className={styles.navyDisclaimerHighlight}>do not provide legal advice</span>, suggestions, or
              representation. SourcePath shares{' '}
              <span className={styles.navyDisclaimerHighlight}>publicly available</span> official sources and{' '}
              <span className={styles.navyDisclaimerHighlight}>cited information</span> tied to specific
              scenarios—not legal advice or recommendations for your case.
            </p>
          </div>
        </header>

        {/* What you can do — action cards, not repeated trust copy */}
        <section className={styles.exploreSection} aria-labelledby="explore-title">
          <h2 id="explore-title" className={styles.blockTitle}>
            What you can do here
          </h2>
          <div className={styles.exploreGrid}>
            {EXPLORE_ACTIONS.map((item) => (
              <Link key={item.to} to={item.to} className={styles.exploreCard}>
                <span className={styles.exploreIcon} aria-hidden>
                  {item.icon}
                </span>
                <span className={styles.exploreTitle}>{item.title}</span>
                <span className={styles.exploreSubtitle}>{item.subtitle}</span>
                <span className={styles.exploreArrow} aria-hidden>
                  →
                </span>
              </Link>
            ))}
          </div>
        </section>

        {/* Principles — boundaries, stated once */}
        <section className={styles.principlesSection} aria-labelledby="principles-title">
          <h2 id="principles-title" className={styles.blockTitle}>
            Our principles
          </h2>
          <p className={styles.blockLead}>Clear boundaries on what this tool is—and is not.</p>
          <div className={styles.principlesGrid}>
            {ABOUT_PRINCIPLES.map((principle) => {
              const isNavy = principle.accent === 'navy'
              return (
                <article key={principle.title} className={styles.principleCard}>
                  <span
                    className={`${styles.principleRail} ${isNavy ? styles.railNavy : styles.railBronze}`}
                    aria-hidden
                  />
                  <span
                    className={`${styles.principleIcon} ${isNavy ? styles.iconNavy : styles.iconBronze}`}
                    aria-hidden
                  >
                    {principle.icon}
                  </span>
                  <h3 className={styles.principleTitle}>{principle.title}</h3>
                  <p className={styles.principleBody}>{principle.description}</p>
                </article>
              )
            })}
          </div>
        </section>

        {/* Source library — single place for citations */}
        <section
          id="sources-library"
          className={styles.sourcesSection}
          aria-labelledby="sources-library-title"
        >
          <div className={styles.sourcesHeader}>
            <div>
              <h2 id="sources-library-title" className={styles.blockTitle}>
                Source library
              </h2>
              <p className={styles.blockLead}>
                {sourceStats.indexed} indexed entries across {sourceStats.families} official source
                families
              </p>
            </div>
            <Link to="/sources#catalog" className={styles.sourcesHeaderCta}>
              Open full library →
            </Link>
          </div>

          <div className={styles.sourcesTable}>
            {previewSources.map((entry) => (
              <Link
                key={entry.id}
                to={`/sources?entry=${entry.id}#catalog`}
                className={styles.sourcesTableRow}
              >
                <span className={styles.sourcesCitation}>{entry.citation}</span>
                <span className={styles.sourcesTopic}>{entry.topic}</span>
                <span className={styles.sourcesFamily}>{familyMeta(entry.family).abbr}</span>
              </Link>
            ))}
          </div>
        </section>

        <section className={styles.legalSection} aria-labelledby="legal-heading">
          <div className={styles.legalBanner}>
            <span className={styles.legalIcon} aria-hidden>
              ⚠
            </span>
            <div>
              <p className={styles.legalEyebrow}>Legal notice</p>
              <h2 id="legal-heading" className={styles.legalHeading}>
                NOT A LAWYER
              </h2>
              <p className={styles.legalBody}>{LEGAL_DISCLAIMER_FULL}</p>
            </div>
          </div>
          <DisclaimerAccordion />
        </section>

        <footer className={styles.pageMeta}>
          <span>
            <strong>{brand.company}</strong> · {brand.name}
          </span>
          <span>General information only — not legal advice</span>
        </footer>
      </div>
    </DashboardLayout>
  )
}
