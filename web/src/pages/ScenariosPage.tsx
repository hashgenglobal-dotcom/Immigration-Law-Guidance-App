import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { BookOpen, Search, X } from 'lucide-react'
import DashboardLayout from '../components/layout/DashboardLayout'
import ScenarioContent from '../components/scenarios/ScenarioContent'
import {
  CATEGORY_BY_ID,
  SCENARIO_CATEGORIES,
  scenarioGuides,
} from '../lib/scenarioGuides'
import type { Scenario, ScenarioCategoryId } from '../lib/scenarioTypes'
import { LEGAL_DISCLAIMER_SHORT } from '../lib/legalCopy'
import styles from './ScenariosPage.module.css'

type CategoryFilter = 'all' | ScenarioCategoryId

function riskClass(level: Scenario['riskLevel']) {
  if (level === 'high') return styles.riskHigh
  if (level === 'medium') return styles.riskMedium
  return styles.riskLow
}

export default function ScenariosPage() {
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<CategoryFilter>('all')
  const [selected, setSelected] = useState<Scenario | null>(null)

  useEffect(() => {
    const id = searchParams.get('s')
    if (!id) return
    const match = scenarioGuides.find((s) => s.id === id)
    if (match) {
      setSelected(match)
      setCategory(match.category)
    }
  }, [searchParams])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return scenarioGuides.filter((s) => {
      const matchesCategory = category === 'all' || s.category === category
      const matchesQuery =
        !q ||
        s.title.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q) ||
        s.content.toLowerCase().includes(q)
      return matchesCategory && matchesQuery
    })
  }, [query, category])

  const grouped = useMemo(() => {
    if (category !== 'all') {
      return [{ id: category, guides: filtered }]
    }
    return SCENARIO_CATEGORIES.map((cat) => ({
      id: cat.id,
      guides: filtered.filter((s) => s.category === cat.id),
    })).filter((g) => g.guides.length > 0)
  }, [filtered, category])

  return (
    <DashboardLayout>
      <div className={styles.page}>
        <header className={styles.header}>
          <p className={styles.eyebrow}>Explore</p>
          <h1 className={styles.title}>Browse scenarios</h1>
          <p className={styles.desc}>
            {scenarioGuides.length} step-by-step guides across {SCENARIO_CATEGORIES.length}{' '}
            categories—overviews, timelines, and links to official sources you can verify.
          </p>
        </header>

        <div className={styles.toolbar}>
          <label className={styles.searchWrap}>
            <Search size={16} className={styles.searchIcon} />
            <input
              type="search"
              placeholder="Search guides…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className={styles.search}
              aria-label="Search guides"
            />
          </label>
          <p className={styles.count}>
            Showing {filtered.length} of {scenarioGuides.length} guides
          </p>
        </div>

        <div className={styles.tabs} role="tablist" aria-label="Scenario categories">
          <button
            type="button"
            role="tab"
            aria-selected={category === 'all'}
            onClick={() => setCategory('all')}
            className={category === 'all' ? `${styles.tab} ${styles.tabActive}` : styles.tab}
          >
            All categories
          </button>
          {SCENARIO_CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              type="button"
              role="tab"
              aria-selected={category === cat.id}
              onClick={() => setCategory(cat.id)}
              className={
                category === cat.id ? `${styles.tab} ${styles.tabActive}` : styles.tab
              }
            >
              {cat.shortLabel}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className={styles.empty}>No guides match your search.</div>
        ) : (
          <div className={styles.sections}>
            {grouped.map((group) => {
              const meta = CATEGORY_BY_ID[group.id as ScenarioCategoryId]
              return (
                <section key={group.id}>
                  {category === 'all' ? (
                    <div className={styles.sectionHead}>
                      <h2 className={styles.sectionTitle}>{meta.label}</h2>
                      <p className={styles.sectionDesc}>{meta.description}</p>
                    </div>
                  ) : null}
                  <div className={styles.grid}>
                    {group.guides.map((scenario) => (
                      <button
                        key={scenario.id}
                        type="button"
                        onClick={() => setSelected(scenario)}
                        className={styles.card}
                      >
                        <div className={styles.cardTop}>
                          <h3 className={styles.cardTitle}>{scenario.title}</h3>
                          <span className={`${styles.risk} ${riskClass(scenario.riskLevel)}`}>
                            {scenario.riskLevel}
                          </span>
                        </div>
                        <p className={styles.cardDesc}>{scenario.description}</p>
                        <span className={styles.cardCta}>Open guide →</span>
                      </button>
                    ))}
                  </div>
                </section>
              )
            })}
          </div>
        )}
      </div>

      {selected ? (
        <div
          className={styles.overlay}
          role="presentation"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) setSelected(null)
          }}
        >
          <div className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="scenario-title">
            <div className={styles.modalHead}>
              <div>
                <p className={styles.modalCategory}>{CATEGORY_BY_ID[selected.category].shortLabel}</p>
                <h2 id="scenario-title" className={styles.modalTitle}>
                  {selected.title}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                aria-label="Close"
                className={styles.modalClose}
              >
                <X size={18} />
              </button>
            </div>

            <div className={styles.modalBody}>
              <p className={styles.modalDescription}>{selected.description}</p>
              <ScenarioContent content={selected.content} />

              {selected.sources.length > 0 ? (
                <section className={styles.sourcesBox}>
                  <h3 className={styles.sourcesTitle}>
                    <BookOpen size={14} />
                    Official sources
                  </h3>
                  <ul className={styles.sourcesList}>
                    {selected.sources.map((src) => (
                      <li key={src.url}>
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={styles.sourceLink}
                        >
                          {src.title}
                        </a>
                        <span className={styles.sourceCitation}> — {src.citation}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}

              <p className={styles.modalDisclaimer}>{LEGAL_DISCLAIMER_SHORT}</p>
            </div>

            <div className={styles.modalFoot}>
              <button type="button" onClick={() => setSelected(null)} className={styles.modalDone}>
                Close
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  )
}
