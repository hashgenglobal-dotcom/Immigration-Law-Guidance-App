import DashboardLayout from '../components/layout/DashboardLayout'

const SOURCE_CATEGORIES = [
  {
    name: 'Code of Federal Regulations',
    abbr: 'CFR / eCFR',
    color: 'var(--blue)',
    colorTint: 'var(--blue-tint)',
    desc: 'Binding agency regulations governing immigration procedures, eligibility, and enforcement. Title 8 covers immigration-specific rules issued by DHS and DOJ.',
    example: '8 CFR § 274a.12 — Employment authorization classes',
    status: 'MVP source',
    detail: ['8 CFR § 208', '8 CFR § 214', '8 CFR § 239', '8 CFR § 244', '8 CFR § 274a.12'],
  },
  {
    name: 'Immigration and Nationality Act',
    abbr: 'INA / U.S. Code',
    color: '#5b4db5',
    colorTint: '#f4f0fb',
    desc: 'Primary statutory authority governing immigration, naturalization, and citizenship. Part of Title 8, U.S. Code — the foundation for all immigration law.',
    example: 'INA § 208 — Asylum eligibility and procedures',
    status: 'MVP source',
    detail: ['INA § 208', 'INA § 274A', 'INA § 316', 'INA § 328–329'],
  },
  {
    name: 'USCIS Forms & Instructions',
    abbr: 'USCIS Forms',
    color: '#2d6a2d',
    colorTint: '#eef6ee',
    desc: 'Official petitions, applications, and their instructions. Instructions are part of the regulatory framework and carry legal weight for adjudications.',
    example: 'Form I-765 — Application for Employment Authorization',
    status: 'MVP source',
    detail: ['I-130', 'I-485', 'I-539', 'I-589', 'I-765', 'N-400'],
  },
  {
    name: 'USCIS Policy Manual',
    abbr: 'Policy Manual',
    color: '#a07830',
    colorTint: '#faf4e8',
    desc: 'Official USCIS guidance for adjudicators. Covers employment authorization, naturalization, public charge, and more across 12+ volumes.',
    example: 'Vol. 10, Part E — Employment Authorization Document procedures',
    status: 'Planned',
    detail: ['Vol. 1 – General Policies', 'Vol. 10 – Employment Authorization', 'Vol. 12 – Naturalization'],
  },
  {
    name: 'BIA Precedent Decisions',
    abbr: 'BIA',
    color: '#b45309',
    colorTint: '#fef3c7',
    desc: 'Board of Immigration Appeals precedent decisions, binding on all immigration judges and DHS officers. Critical for asylum, removal, and relief cases.',
    example: 'Matter of X — Credibility standards in asylum proceedings',
    status: 'Planned',
    detail: [],
  },
  {
    name: 'Federal Register',
    abbr: 'Fed. Register',
    color: '#0f7ba7',
    colorTint: '#e0f2fe',
    desc: 'Official journal of the U.S. government — immigration rulemaking, proposed rules, TPS designations, and DHS/DOJ agency notices with legal effect.',
    example: 'TPS extension and redesignation notices; fee schedule rules',
    status: 'Planned',
    detail: [],
  },
]

const STATUS_STYLE: Record<string, { background: string; color: string }> = {
  'MVP source': { background: '#eef6ee', color: '#2d6a2d' },
  'Planned': { background: 'var(--blue-tint)', color: 'var(--blue)' },
}

export default function SourcesPage() {
  return (
    <DashboardLayout>
      <div style={{ padding: '28px 32px' }}>
        {/* Header */}
        <div style={{ marginBottom: 24, maxWidth: 680 }}>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: 'var(--text)',
              marginBottom: 6,
              letterSpacing: '-0.02em',
            }}
          >
            Sources
          </h1>
          <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.65 }}>
            The guidance tool draws from these official primary sources. Every answer cites its
            sources inline so you can verify the information directly. Source transparency is a
            core design principle of this tool.
          </p>
        </div>

        {/* Search placeholder */}
        <div style={{ marginBottom: 24, maxWidth: 360 }}>
          <input
            disabled
            placeholder="Search sources… (coming soon)"
            style={{
              width: '100%',
              padding: '9px 14px',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              fontSize: 13.5,
              color: 'var(--text-muted)',
              background: 'var(--surface)',
              fontFamily: 'inherit',
              cursor: 'not-allowed',
              outline: 'none',
            }}
          />
        </div>

        {/* Two-column grid of source categories */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 16,
            marginBottom: 32,
          }}
        >
          {SOURCE_CATEGORIES.map((cat) => (
            <div
              key={cat.name}
              style={{
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderTop: `3px solid ${cat.color}`,
                borderRadius: 'var(--radius-lg)',
                padding: '20px 20px',
                display: 'flex',
                flexDirection: 'column',
                gap: 10,
              }}
            >
              {/* Header row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                <div>
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 11.5,
                      fontWeight: 700,
                      color: cat.color,
                      marginBottom: 3,
                    }}
                  >
                    {cat.abbr}
                  </div>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 700,
                      color: 'var(--text)',
                      lineHeight: 1.3,
                    }}
                  >
                    {cat.name}
                  </div>
                </div>
                <span
                  style={{
                    fontSize: 10.5,
                    fontWeight: 700,
                    padding: '3px 9px',
                    borderRadius: 99,
                    whiteSpace: 'nowrap',
                    flexShrink: 0,
                    ...STATUS_STYLE[cat.status],
                  }}
                >
                  {cat.status}
                </span>
              </div>

              {/* Description */}
              <p
                style={{
                  fontSize: 12.5,
                  color: 'var(--text-secondary)',
                  lineHeight: 1.65,
                  margin: 0,
                }}
              >
                {cat.desc}
              </p>

              {/* Example citation */}
              <div
                style={{
                  padding: '8px 12px',
                  background: cat.colorTint,
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 11.5,
                  color: cat.color,
                  fontFamily: 'var(--font-mono)',
                  lineHeight: 1.5,
                }}
              >
                {cat.example}
              </div>

              {/* Indexed items */}
              {cat.detail.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {cat.detail.map((d) => (
                    <span
                      key={d}
                      style={{
                        fontSize: 11,
                        padding: '2px 8px',
                        background: 'var(--bg)',
                        border: '1px solid var(--border)',
                        borderRadius: 4,
                        color: 'var(--text-secondary)',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      {d}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <div
          style={{
            padding: '13px 18px',
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            fontSize: 12.5,
            color: 'var(--text-muted)',
            lineHeight: 1.6,
          }}
        >
          Additional sources including USCIS Policy Manual volumes, BIA precedent decisions, and
          Federal Register notices will be indexed and connected in Milestone 2.
        </div>
      </div>
    </DashboardLayout>
  )
}
