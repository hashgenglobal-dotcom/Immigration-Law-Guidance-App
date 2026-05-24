import { useState } from 'react'
import DashboardLayout from '../components/layout/DashboardLayout'

type Category = 'All' | 'USCIS' | 'Federal Register' | 'BIA'

const CATEGORIES: Category[] = ['All', 'USCIS', 'Federal Register', 'BIA']

const PLACEHOLDER_UPDATES = [
  {
    category: 'USCIS' as Category,
    tag: 'Policy Manual',
    tagColor: 'var(--blue)',
    tagTint: 'var(--blue-tint)',
    date: 'Coming soon',
    title: 'USCIS Policy Manual — Employment Authorization Updates',
    desc: 'Recent changes to Part A (Public Charge) and Part E (Employment Authorization) chapters. Affects EAD eligibility timelines for asylum applicants and parolees.',
  },
  {
    category: 'USCIS' as Category,
    tag: 'Form Update',
    tagColor: '#2d6a2d',
    tagTint: '#eef6ee',
    date: 'Coming soon',
    title: 'Form I-765 Instructions Revised',
    desc: 'USCIS updated instructions for Form I-765 (Employment Authorization). New eligibility category codes added for parolees and Afghan special immigrants.',
  },
  {
    category: 'Federal Register' as Category,
    tag: 'Proposed Rule',
    tagColor: '#0f7ba7',
    tagTint: '#e0f2fe',
    date: 'Coming soon',
    title: 'Proposed Rule: Fee Schedule Adjustment',
    desc: 'DHS published a proposed rule to adjust filing fees for immigration benefits. 60-day comment period following publication in the Federal Register.',
  },
  {
    category: 'Federal Register' as Category,
    tag: 'Final Rule',
    tagColor: '#0f7ba7',
    tagTint: '#e0f2fe',
    date: 'Coming soon',
    title: 'Final Rule: Temporary Protected Status Designation',
    desc: 'DHS published a final rule extending and redesignating TPS for eligible nationals. See Federal Register Vol. 89 for full text and effective dates.',
  },
  {
    category: 'BIA' as Category,
    tag: 'Precedent Decision',
    tagColor: '#5b4db5',
    tagTint: '#f4f0fb',
    date: 'Coming soon',
    title: 'Matter of X — Asylum Credibility Standards',
    desc: 'Board of Immigration Appeals issued a precedent decision clarifying standards for credibility determinations in asylum proceedings under INA § 208.',
  },
  {
    category: 'BIA' as Category,
    tag: 'Precedent Decision',
    tagColor: '#5b4db5',
    tagTint: '#f4f0fb',
    date: 'Coming soon',
    title: 'Cancellation of Removal — Continuous Presence',
    desc: 'BIA clarified the "stop-time" rule for cancellation of removal under INA § 240A, addressing absences and their effect on continuous physical presence.',
  },
]

const COVERAGE_SOURCES = [
  { label: 'USCIS Policy Manual', status: 'Milestone 2', color: 'var(--blue)' },
  { label: 'USCIS Forms & Instructions', status: 'Milestone 2', color: 'var(--blue)' },
  { label: 'Federal Register Notices', status: 'Milestone 2', color: '#0f7ba7' },
  { label: 'BIA Precedent Decisions', status: 'Milestone 2', color: '#5b4db5' },
  { label: 'EOIR Policy Memos', status: 'Planned', color: '#a07830' },
]

export default function OfficialUpdatesPage() {
  const [active, setActive] = useState<Category>('All')

  const filtered =
    active === 'All' ? PLACEHOLDER_UPDATES : PLACEHOLDER_UPDATES.filter((u) => u.category === active)

  return (
    <DashboardLayout>
      <div style={{ padding: '28px 32px' }}>
        {/* Header */}
        <div style={{ marginBottom: 24, maxWidth: 640 }}>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: 'var(--text)',
              marginBottom: 6,
              letterSpacing: '-0.02em',
            }}
          >
            Official Updates
          </h1>
          <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.65 }}>
            Curated immigration law updates from USCIS, the Federal Register, and the Board of
            Immigration Appeals. Backend integration is coming in Milestone 2 — cards below are
            illustrative.
          </p>
        </div>

        {/* Filter chips */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActive(cat)}
              style={{
                padding: '6px 16px',
                borderRadius: 99,
                border: active === cat ? '1.5px solid var(--navy)' : '1px solid var(--border)',
                background: active === cat ? 'var(--navy)' : 'var(--surface)',
                color: active === cat ? '#ffffff' : 'var(--text-secondary)',
                fontSize: 12.5,
                fontWeight: active === cat ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Two-column layout */}
        <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
          {/* Left: update cards */}
          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
            {filtered.map((item) => (
              <div
                key={item.title}
                style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderLeft: `3px solid ${item.tagColor}`,
                  borderRadius: 'var(--radius-lg)',
                  padding: '18px 20px',
                  opacity: 0.78,
                }}
              >
                <div
                  style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}
                >
                  <span
                    style={{
                      fontSize: 10.5,
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.07em',
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: item.tagTint,
                      color: item.tagColor,
                    }}
                  >
                    {item.tag}
                  </span>
                  <span
                    style={{ fontSize: 11.5, color: 'var(--text-muted)', fontWeight: 500 }}
                  >
                    {item.date}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: 'var(--text)',
                    marginBottom: 6,
                    lineHeight: 1.35,
                  }}
                >
                  {item.title}
                </div>
                <div
                  style={{
                    fontSize: 13,
                    color: 'var(--text-secondary)',
                    lineHeight: 1.65,
                  }}
                >
                  {item.desc}
                </div>
              </div>
            ))}
          </div>

          {/* Right: milestone + coverage panel */}
          <div style={{ width: 268, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Milestone 2 notice */}
            <div
              style={{
                background: 'var(--blue-tint)',
                border: '1px solid rgba(59,110,165,0.22)',
                borderRadius: 'var(--radius-lg)',
                padding: '18px 18px',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--blue)',
                  marginBottom: 8,
                }}
              >
                Coming in Milestone 2
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.65 }}>
                Live update fetching from USCIS RSS feeds, Federal Register API, and BIA
                decisions will be connected in a future release.
              </p>
            </div>

            {/* Coverage panel */}
            <div
              style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-lg)',
                padding: '16px 18px',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--text-muted)',
                  marginBottom: 12,
                }}
              >
                Update coverage
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                {COVERAGE_SOURCES.map((s) => (
                  <div
                    key={s.label}
                    style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                  >
                    <span style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>
                      {s.label}
                    </span>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        padding: '2px 8px',
                        borderRadius: 99,
                        background: 'var(--blue-tint)',
                        color: 'var(--blue)',
                      }}
                    >
                      {s.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Disclaimer note */}
            <div
              style={{
                fontSize: 11.5,
                color: 'var(--text-muted)',
                lineHeight: 1.6,
                padding: '12px 14px',
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
              }}
            >
              Cards above are illustrative placeholders and do not represent current law or policy.
              Verify all immigration information with official USCIS, DOJ, or Federal Register sources.
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
