import { CheckCircle, ExternalLink, FileText } from 'lucide-react'
import { useState } from 'react'
import type { StructuredResultResponse } from '../../lib/api'
import styles from './StructuredResultCard.module.css'

type Props = {
  result: StructuredResultResponse
}

export default function StructuredResultCard({ result }: Props) {
  const [citationsOpen, setCitationsOpen] = useState(false)

  return (
    <div className={styles.wrap}>
      <div className={styles.shortAnswer}>
        <div className={styles.shortAnswerInner}>
          <div className={styles.shortAnswerLabel}>Short answer</div>
          <p className={styles.shortAnswerText}>{result.short_answer}</p>
        </div>
      </div>

      {result.eligibility_checklist.length > 0 ? (
        <section className={styles.section}>
          <h4 className={styles.sectionTitle}>Eligibility checklist</h4>
          <ul className={styles.list}>
            {result.eligibility_checklist.map((item, idx) => (
              <li key={`${idx}-${item}`} className={styles.listItem}>
                <CheckCircle size={16} className={styles.checkIcon} />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {result.next_steps.length > 0 ? (
        <section className={styles.section}>
          <h4 className={styles.sectionTitle}>Next steps</h4>
          <ol className={styles.steps}>
            {result.next_steps.map((step, idx) => (
              <li key={`${idx}-${step}`} className={styles.stepRow}>
                <div className={styles.stepBadge}>{idx + 1}</div>
                <p className={styles.stepText}>{step}</p>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      <section className={styles.section}>
        <button
          type="button"
          className={styles.citationsToggle}
          onClick={() => setCitationsOpen((v) => !v)}
        >
          <span className={styles.citationsTitle}>
            <FileText size={15} />
            Official Legal References
          </span>
          <span className={styles.citationsMeta}>
            {citationsOpen ? 'Hide' : 'Show'} ({result.citations.length})
          </span>
        </button>

        {citationsOpen ? (
          result.citations.length > 0 ? (
            <div className={styles.citationsList}>
              {result.citations.map((citation, idx) => (
                <article key={`${idx}-${citation.title}`} className={styles.citationCard}>
                  <div className={styles.citationHeader}>
                    <h5 className={styles.citationTitle}>{citation.title}</h5>
                    {citation.url ? (
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.citationLink}
                      >
                        Source
                        <ExternalLink size={12} />
                      </a>
                    ) : null}
                  </div>
                  <blockquote className={styles.snippet}>{citation.snippet}</blockquote>
                </article>
              ))}
            </div>
          ) : (
            <p className={styles.emptyCitations}>No citations returned for this answer.</p>
          )
        ) : null}
      </section>

      <p className={styles.disclaimer}>{result.disclaimer}</p>
    </div>
  )
}
