import { useEffect, useMemo, useState } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'
import DashboardLayout from '../components/layout/DashboardLayout'
import {
  SOURCE_CATALOG,
  SOURCE_FAMILIES,
  catalogStats,
  familyMeta,
  type SourceEntry,
  type SourceFamily,
} from '../lib/sourceCatalog'
import styles from './SourcesPage.module.css'

type FamilyFilter = 'all' | SourceFamily

function statusClass(status: SourceEntry['status']) {
  if (status === 'indexed') return styles.statusIndexed
  if (status === 'preview') return styles.statusPreview
  return styles.statusPlanned
}

export default function SourcesPage() {
  const location = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [query, setQuery] = useState('')
  const [familyFilter, setFamilyFilter] = useState<FamilyFilter>('all')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const stats = catalogStats()

  useEffect(() => {
    const family = searchParams.get('family') as SourceFamily | null
    if (family && SOURCE_FAMILIES.some((f) => f.id === family)) {
      setFamilyFilter(family)
    }
    const entryId = searchParams.get('entry')
    if (entryId && SOURCE_CATALOG.some((e) => e.id === entryId)) {
      setSelectedId(entryId)
    }
  }, [searchParams])

  useEffect(() => {
    if (location.hash === '#cited' || location.hash === '#catalog') {
      const id = location.hash.slice(1)
      requestAnimationFrame(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    }
  }, [location.hash])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return SOURCE_CATALOG.filter((entry) => {
      const matchesFamily = familyFilter === 'all' || entry.family === familyFilter
      if (!matchesFamily) return false
      if (!q) return true
      const haystack = [
        entry.citation,
        entry.topic,
        entry.subtopic,
        entry.description,
        familyMeta(entry.family).name,
        familyMeta(entry.family).abbr,
        ...entry.tags,
      ]
        .join(' ')
        .toLowerCase()
      return haystack.includes(q)
    })
  }, [query, familyFilter])

  const selected =
    filtered.find((e) => e.id === selectedId) ??
    SOURCE_CATALOG.find((e) => e.id === selectedId) ??
    filtered[0] ??
    null

  useEffect(() => {
    if (filtered.length === 0) {
      setSelectedId(null)
      return
    }
    if (!selectedId || !filtered.some((e) => e.id === selectedId)) {
      setSelectedId(filtered[0].id)
    }
  }, [filtered, selectedId])

  function setFilter(next: FamilyFilter) {
    setFamilyFilter(next)
    if (next === 'all') {
      searchParams.delete('family')
    } else {
      searchParams.set('family', next)
    }
    setSearchParams(searchParams, { replace: true })
  }

  return (
    <DashboardLayout>
      <div className={styles.page}>
        <header className={styles.header}>
          <p className={styles.eyebrow}>Source library</p>
          <h1 className={styles.title}>Sources</h1>
          <p className={styles.desc}>
            Browse the official materials behind every cited answer—CFR, INA, USCIS policy, forms, and
            agency pages indexed for verifiable navigation.
          </p>
        </header>

        <div className={styles.statsRow}>
          <span className={styles.stat}>
            <strong>{stats.total}</strong> catalog entries
          </span>
          <span className={styles.stat}>
            <strong>{stats.indexed}</strong> indexed for retrieval
          </span>
          <span className={styles.stat}>
            <strong>{stats.families}</strong> source families
          </span>
        </div>

        <section id="cited" className={styles.citedSection} aria-labelledby="cited-title">
          <h2 id="cited-title" className={styles.citedTitle}>
            How citations work
          </h2>
          <p className={styles.citedBody}>
            When you ask a question, SourcePath retrieves relevant passages from the active legal
            corpus (eCFR Title 8, INA, USCIS Policy Manual, and related official pages). The
            assistant surfaces citations inline—each maps to a source record you can open on the
            official government site.
          </p>
          <ul className={styles.citedList}>
            <li>
              <strong>Citation</strong> — the legal reference (e.g. 8 CFR § 208.7, INA § 208, Form
              I-765).
            </li>
            <li>
              <strong>Topic / subtopic</strong> — how the chunk is classified in our index for search
              and display.
            </li>
            <li>
              <strong>Official URL</strong> — link to eCFR, USCIS.gov, or the U.S. Code for primary
              source verification.
            </li>
            <li>
              <strong>Snippet</strong> — retrieved text shown in chat (from the database, not model
              memory).
            </li>
          </ul>
        </section>

        <div id="catalog" className={styles.toolbar}>
          <label className={styles.searchWrap}>
            <span className="sr-only">Search sources</span>
            <input
              type="search"
              className={styles.search}
              placeholder="Search by citation, topic, or tag…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <div className={styles.filters} role="group" aria-label="Filter by source family">
            <button
              type="button"
              className={
                familyFilter === 'all'
                  ? `${styles.filterBtn} ${styles.filterActive}`
                  : styles.filterBtn
              }
              onClick={() => setFilter('all')}
            >
              All
            </button>
            {SOURCE_FAMILIES.filter((f) => f.status !== 'planned').map((f) => (
              <button
                key={f.id}
                type="button"
                className={
                  familyFilter === f.id
                    ? `${styles.filterBtn} ${styles.filterActive}`
                    : styles.filterBtn
                }
                onClick={() => setFilter(f.id)}
              >
                {f.abbr}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.layout}>
          <div className={styles.catalog} role="region" aria-label="Source catalog">
            <div className={styles.catalogHead}>
              <span>Citation / topic</span>
              <span>Family</span>
              <span>Status</span>
            </div>
            {filtered.length === 0 ? (
              <p className={styles.empty}>No sources match your search. Try a different term or filter.</p>
            ) : (
              filtered.map((entry) => (
                <button
                  key={entry.id}
                  type="button"
                  className={
                    selected?.id === entry.id
                      ? `${styles.catalogRow} ${styles.rowSelected}`
                      : styles.catalogRow
                  }
                  onClick={() => setSelectedId(entry.id)}
                  aria-pressed={selected?.id === entry.id}
                >
                  <span>
                    <span className={styles.rowCitation}>{entry.citation}</span>
                    <span className={styles.rowTopic}>
                      {entry.topic} · {entry.subtopic}
                    </span>
                  </span>
                  <span className={styles.rowFamily}>{familyMeta(entry.family).abbr}</span>
                  <span className={`${styles.statusBadge} ${statusClass(entry.status)}`}>
                    {entry.status}
                  </span>
                </button>
              ))
            )}
          </div>

          <aside className={styles.detail} aria-label="Source details">
            {selected ? (
              <>
                <p className={styles.detailCitation}>{selected.citation}</p>
                <p className={styles.detailMeta}>
                  {familyMeta(selected.family).name} · {selected.topic} · {selected.subtopic}
                </p>
                <p className={styles.detailDesc}>{selected.description}</p>
                <div className={styles.detailTags}>
                  {selected.tags.map((tag) => (
                    <span key={tag} className={styles.tag}>
                      {tag}
                    </span>
                  ))}
                </div>
                <span className={`${styles.statusBadge} ${statusClass(selected.status)}`}>
                  {selected.status}
                </span>
                <p className={styles.detailDesc} style={{ marginTop: 14, marginBottom: 0 }}>
                  <a
                    href={selected.officialUrl}
                    className={styles.officialLink}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Open official source ↗
                  </a>
                </p>
              </>
            ) : (
              <p className={styles.detailEmpty}>Select a source from the catalog to view full details.</p>
            )}
          </aside>
        </div>

        <section className={styles.familiesSection} aria-labelledby="families-title">
          <h2 id="families-title" className={styles.familiesTitle}>
            Source families in the corpus
          </h2>
          <div className={styles.familiesGrid}>
            {SOURCE_FAMILIES.map((f) => (
              <article
                key={f.id}
                className={styles.familyCard}
                style={{ ['--family-color' as string]: f.color }}
              >
                <p className={styles.familyAbbr}>{f.abbr}</p>
                <h3 className={styles.familyName}>{f.name}</h3>
                <p className={styles.familyDesc}>{f.description}</p>
                <p className={styles.familyNote}>{f.corpusNote}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </DashboardLayout>
  )
}
