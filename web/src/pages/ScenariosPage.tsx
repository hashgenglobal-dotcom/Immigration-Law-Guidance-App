import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import DashboardLayout from '../components/layout/DashboardLayout'
import { scenarioGuides } from '../lib/scenarioGuides'
import type { Scenario } from '../lib/scenarioTypes'
import { LEGAL_DISCLAIMER_SHORT } from '../lib/legalCopy'
import styles from './ScenariosPage.module.css'

type RiskFilter = 'all' | Scenario['riskLevel']

function riskClass(level: Scenario['riskLevel']) {
  if (level === 'high') return styles.riskHigh
  if (level === 'medium') return styles.riskMedium
  return styles.riskLow
}

export default function ScenariosPage() {
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState('')
  const [riskFilter, setRiskFilter] = useState<RiskFilter>('all')
  const [selected, setSelected] = useState<Scenario | null>(null)

  useEffect(() => {
    const id = searchParams.get('s')
    if (!id) return
    const match = scenarioGuides.find((s) => s.id === id)
    if (match) setSelected(match)
  }, [searchParams])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return scenarioGuides.filter((s) => {
      const matchesRisk = riskFilter === 'all' || s.riskLevel === riskFilter
      const matchesQuery =
        !q ||
        s.title.toLowerCase().includes(q) ||
        s.shortDescription.toLowerCase().includes(q) ||
        s.overview.toLowerCase().includes(q)
      return matchesRisk && matchesQuery
    })
  }, [query, riskFilter])

  return (
    <DashboardLayout>
      <div className={styles.page}>
        <header className={styles.header}>
          <p className={styles.eyebrow}>Explore</p>
          <h1 className={styles.title}>Browse scenarios</h1>
          <p className={styles.desc}>
            Step-by-step guides for common immigration situations. These are general guides—consult an
            attorney for advice about your specific case.
          </p>
        </header>

        <div className={styles.toolbar}>
          <label className={styles.searchWrap}>
            <span className="sr-only">Search scenarios</span>
            <input
              type="search"
              className={styles.search}
              placeholder="Search by topic…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <div className={styles.filters} role="group" aria-label="Filter by risk">
            {(['all', 'low', 'medium', 'high'] as const).map((level) => (
              <button
                key={level}
                type="button"
                className={
                  riskFilter === level
                    ? `${styles.filterBtn} ${styles.filterActive}`
                    : styles.filterBtn
                }
                onClick={() => setRiskFilter(level)}
              >
                {level === 'all' ? 'All' : level}
              </button>
            ))}
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className={styles.empty}>No scenarios match your search.</div>
        ) : (
          <div className={styles.grid}>
            {filtered.map((scenario) => (
              <button
                key={scenario.id}
                type="button"
                className={styles.card}
                onClick={() => setSelected(scenario)}
              >
                <div className={styles.cardTop}>
                  <h2 className={styles.cardTitle}>{scenario.title}</h2>
                  <span className={`${styles.risk} ${riskClass(scenario.riskLevel)}`}>
                    {scenario.riskLevel}
                  </span>
                </div>
                <p className={styles.cardDesc}>{scenario.shortDescription}</p>
                <span className={styles.cardCta}>Open guide →</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {selected ? (
        <div
          className={styles.modalOverlay}
          role="presentation"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setSelected(null)
          }}
        >
          <div className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="scenario-title">
            <div className={styles.modalHead}>
              <h2 id="scenario-title" className={styles.modalTitle}>
                {selected.title}
              </h2>
              <button type="button" className={styles.modalClose} onClick={() => setSelected(null)} aria-label="Close">
                ×
              </button>
            </div>
            <span className={`${styles.risk} ${riskClass(selected.riskLevel)}`}>{selected.riskLevel} risk</span>
            <section className={styles.modalSection}>
              <h3 className={styles.modalLabel}>Overview</h3>
              <p>{selected.overview}</p>
            </section>
            <section className={styles.modalSection}>
              <h3 className={styles.modalLabel}>Steps and key points</h3>
              <ul className={styles.bullets}>
                {selected.keyPoints.map((point, i) => (
                  <li key={i}>{point}</li>
                ))}
              </ul>
            </section>
            {selected.sources.length > 0 ? (
              <section className={styles.modalSection}>
                <h3 className={styles.modalLabel}>Official sources</h3>
                <ul className={styles.sources}>
                  {selected.sources.map((src) => (
                    <li key={src.url}>
                      <a href={src.url} target="_blank" rel="noopener noreferrer">
                        {src.title}
                      </a>
                      <span className={styles.citation}> — {src.citation}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}
            <p className={styles.modalDisclaimer}>{LEGAL_DISCLAIMER_SHORT}</p>
            <button type="button" className={styles.modalDone} onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  )
}
