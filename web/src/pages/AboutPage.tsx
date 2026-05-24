import DashboardLayout from '../components/layout/DashboardLayout'

const INFO_CARDS = [
  {
    icon: '◈',
    heading: 'What this tool does',
    bullets: [
      'Answers questions about U.S. immigration processes',
      'Grounds every answer in official federal sources',
      'Cites specific regulations, forms, and statutes inline',
      'Handles multi-turn follow-up questions in context',
    ],
  },
  {
    icon: '✕',
    heading: 'What this tool does not do',
    bullets: [
      'Provide legal advice or legal representation',
      'Evaluate individual case facts or predict outcomes',
      'Create an attorney-client relationship',
      'Substitute for a qualified immigration attorney',
    ],
  },
  {
    icon: '◉',
    heading: 'How answers are generated',
    bullets: [
      'Semantic search over official immigration documents',
      'Broad questions trigger a guided intake category flow',
      'Language model synthesizes from retrieved passages',
      'All answers include inline source citations',
    ],
  },
  {
    icon: '○',
    heading: 'Privacy & data handling',
    bullets: [
      'Conversation context is session-based only',
      'No data saved to a database or external service',
      'New conversation discards all prior context',
      'No user accounts or login required',
    ],
  },
]

const CAPABILITIES = [
  { label: 'EAD / Work authorization', status: 'Supported' },
  { label: 'Asylum applications (I-589)', status: 'Supported' },
  { label: 'Adjustment of Status (I-485)', status: 'Supported' },
  { label: 'Naturalization (N-400)', status: 'Supported' },
  { label: 'TPS & DACA', status: 'Supported' },
  { label: 'F-1 / OPT / STEM OPT', status: 'Supported' },
  { label: 'Official updates feed', status: 'Milestone 2' },
  { label: 'Case tracking / document storage', status: 'Not planned' },
  { label: 'Legal advice or representation', status: 'Out of scope' },
]

const STATUS_STYLE: Record<string, { background: string; color: string }> = {
  Supported: { background: '#eef6ee', color: '#2d6a2d' },
  'Milestone 2': { background: 'var(--blue-tint)', color: 'var(--blue)' },
  'Not planned': { background: 'var(--bg)', color: 'var(--text-muted)' },
  'Out of scope': { background: 'var(--bg)', color: 'var(--text-muted)' },
}

export default function AboutPage() {
  return (
    <DashboardLayout>
      <div style={{ padding: '28px 32px' }}>
        {/* Header */}
        <div style={{ marginBottom: 28, maxWidth: 640 }}>
          <h1
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: 'var(--text)',
              marginBottom: 6,
              letterSpacing: '-0.02em',
            }}
          >
            About
          </h1>
          <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.65 }}>
            An informational tool for U.S. immigration questions grounded in official primary
            sources. Not a substitute for qualified legal counsel.
          </p>
        </div>

        {/* Two-column: left content + right panel */}
        <div style={{ display: 'flex', gap: 28, alignItems: 'flex-start' }}>
          {/* Left column */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* 2x2 info cards */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: 14,
                marginBottom: 28,
              }}
            >
              {INFO_CARDS.map((card) => (
                <div
                  key={card.heading}
                  style={{
                    background: 'var(--surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '20px 20px',
                  }}
                >
                  <div
                    style={{
                      fontSize: 18,
                      color: 'var(--navy)',
                      marginBottom: 10,
                      lineHeight: 1,
                      opacity: 0.7,
                    }}
                  >
                    {card.icon}
                  </div>
                  <h2
                    style={{
                      fontSize: 13.5,
                      fontWeight: 700,
                      color: 'var(--text)',
                      marginBottom: 12,
                      lineHeight: 1.3,
                    }}
                  >
                    {card.heading}
                  </h2>
                  <ul
                    style={{
                      paddingLeft: 0,
                      listStyle: 'none',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 7,
                    }}
                  >
                    {card.bullets.map((b) => (
                      <li
                        key={b}
                        style={{
                          display: 'flex',
                          gap: 8,
                          fontSize: 13,
                          color: 'var(--text-secondary)',
                          lineHeight: 1.5,
                        }}
                      >
                        <span
                          style={{
                            color: 'var(--text-muted)',
                            flexShrink: 0,
                            marginTop: 1,
                            fontSize: 12,
                          }}
                        >
                          ·
                        </span>
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            {/* Capabilities table */}
            <div>
              <h2
                style={{
                  fontSize: 14,
                  fontWeight: 700,
                  color: 'var(--text)',
                  marginBottom: 14,
                }}
              >
                Scope &amp; capabilities
              </h2>
              <div
                style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-lg)',
                  overflow: 'hidden',
                }}
              >
                {CAPABILITIES.map((c, i) => (
                  <div
                    key={c.label}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '11px 18px',
                      borderBottom:
                        i < CAPABILITIES.length - 1 ? '1px solid var(--border-light)' : 'none',
                      background: i % 2 === 0 ? '#ffffff' : '#fafbfc',
                    }}
                  >
                    <span style={{ fontSize: 13, color: 'var(--text)' }}>{c.label}</span>
                    <span
                      style={{
                        fontSize: 11.5,
                        fontWeight: 600,
                        padding: '2px 10px',
                        borderRadius: 99,
                        ...STATUS_STYLE[c.status],
                      }}
                    >
                      {c.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right panel */}
          <div
            style={{
              width: 268,
              flexShrink: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
            }}
          >
            {/* Prominent disclaimer */}
            <div
              style={{
                padding: '20px',
                background: 'var(--bronze-tint)',
                border: '1px solid rgba(160, 120, 48, 0.28)',
                borderRadius: 'var(--radius-lg)',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--bronze)',
                  marginBottom: 10,
                }}
              >
                Legal Disclaimer
              </div>
              <p style={{ fontSize: 13, color: 'var(--bronze)', lineHeight: 1.7 }}>
                This app provides legal information and guidance,{' '}
                <strong>not legal advice</strong>. For personal legal decisions — including asylum,
                removal proceedings, visa petitions, or naturalization — consult a qualified
                immigration attorney.
              </p>
            </div>

            {/* Quick facts */}
            <div
              style={{
                padding: '18px 20px',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-lg)',
              }}
            >
              <div
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: 'var(--text-muted)',
                  marginBottom: 14,
                }}
              >
                Quick Facts
              </div>
              {[
                { label: 'Official sources', value: '15+ indexed' },
                { label: 'Data storage', value: 'Session-based only' },
                { label: 'Legal status', value: 'Informational only' },
                { label: 'Milestone', value: 'Web MVP · M1' },
              ].map((fact) => (
                <div
                  key={fact.label}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 10,
                    gap: 8,
                  }}
                >
                  <span style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                    {fact.label}
                  </span>
                  <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {fact.value}
                  </span>
                </div>
              ))}
            </div>

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
              Immigration Law Guidance · Web MVP
              <br />
              Milestone 1 — informational tool only.
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
