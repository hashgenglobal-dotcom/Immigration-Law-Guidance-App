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
import { ABOUT_NAVY_LEGAL_NOTICE_LABEL } from '../lib/legalCopy'
import { ABOUT_NAVY_LEGAL_SHORT } from '../lib/productMessaging'
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
              {'category' in ABOUT_MISSION ? (
                <p className={styles.missionCategory}>{ABOUT_MISSION.category}</p>
              ) : null}
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
            <p className={styles.navyDisclaimerText}>{ABOUT_NAVY_LEGAL_SHORT}</p>
            <a href="#full-legal-notice" className={styles.navyDisclaimerLink}>
              Full legal notice
            </a>
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
            How SourcePath works
          </h2>
          <p className={styles.blockLead}>
            Retrieval-first navigation with clear boundaries—not a chatbot that guesses.
          </p>
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

        <section
          id="full-legal-notice"
          className={styles.legalSection}
          aria-labelledby="legal-heading"
        >
          <h2 id="legal-heading" className={styles.blockTitle}>
            Legal notice
          </h2>
          <p className={styles.blockLead}>
            Compliance details for using SourcePath as an information tool.
          </p>
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
