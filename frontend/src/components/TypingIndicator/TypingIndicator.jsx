import styles from './TypingIndicator.module.css'

export default function TypingIndicator({ accent }) {
  return (
    <div className={styles.row}>
      <div className={styles.bubble}>
        <span className={styles.dot} style={{ '--accent': accent, animationDelay: '0ms' }} />
        <span className={styles.dot} style={{ '--accent': accent, animationDelay: '150ms' }} />
        <span className={styles.dot} style={{ '--accent': accent, animationDelay: '300ms' }} />
      </div>
    </div>
  )
}
