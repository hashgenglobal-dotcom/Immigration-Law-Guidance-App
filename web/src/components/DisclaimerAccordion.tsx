import { useState } from 'react'
import { LEGAL_DISCLAIMER_FULL, LEGAL_DISCLAIMER_SHORT } from '../lib/legalCopy'
import styles from './DisclaimerAccordion.module.css'

export default function DisclaimerAccordion() {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={styles.wrap}>
      <button
        type="button"
        className={styles.banner}
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className={styles.row}>
          <span className={styles.iconCircle} aria-hidden>
            ℹ
          </span>
          <div className={styles.textCol}>
            <div className={styles.heading}>Important Information</div>
            {!expanded ? <p className={styles.preview}>{LEGAL_DISCLAIMER_SHORT}</p> : null}
          </div>
          <span className={styles.chevron} aria-hidden>
            {expanded ? '▲' : '▼'}
          </span>
        </div>
        {!expanded ? <p className={styles.tapHint}>Tap to read full disclaimer</p> : null}
        {expanded ? <div className={styles.expanded}>{LEGAL_DISCLAIMER_FULL}</div> : null}
      </button>
    </div>
  )
}
