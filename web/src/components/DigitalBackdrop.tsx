import styles from './DigitalBackdrop.module.css'

export default function DigitalBackdrop() {
  return (
    <div className={styles.backdrop} aria-hidden>
      <div className={styles.washTop} />
      <div className={styles.washBottom} />
      <div className={styles.dots} />
    </div>
  )
}
