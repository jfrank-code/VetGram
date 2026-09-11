import CompareRunner from '../CompareRunner/CompareRunner.jsx'
import styles from './MessageBubble.module.css'

const STATUS_LIGHT = { unsafe: 'red', safe: 'green', depends: 'amber' }
const STATUS_LABEL = { unsafe: 'Unsafe', safe: 'Safe', depends: 'Depends' }

function ToxicityCard({ reply, accent }) {
  return (
    <div className={styles.card} style={{ '--accent': accent }}>
      <div className={styles.toxList}>
        {reply.items.map((item, i) => (
          <div className={styles.toxItem} key={`${item.name}-${i}`}>
            <span className={`${styles.light} ${styles[STATUS_LIGHT[item.status]]}`} />
            <span className={styles.cardMeta}>
              <span className={styles.toxName}>{item.name}</span>
              <b>{STATUS_LABEL[item.status]}:</b> {item.note}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function DietCard({ reply, accent }) {
  return (
    <div className={styles.card} style={{ '--accent': accent }}>
      <p className={styles.dietText}>
        For a {reply.weight_kg} kg {reply.species} ({reply.life_stage.replace('_', '/')},{' '}
        {reply.activity_level} activity), here's the daily target:
      </p>
      <div className={styles.readout}>
        <div>
          <div className={styles.readoutLabel}>Resting energy (RER)</div>
          <div className={styles.readoutValue}>{reply.rer_kcal} kcal</div>
        </div>
        <div>
          <div className={styles.readoutLabel}>Daily target (MER)</div>
          <div className={styles.readoutValue}>{reply.mer_kcal} kcal</div>
        </div>
      </div>
      {reply.explanation && <p className={styles.dietExplanation}>{reply.explanation}</p>}
    </div>
  )
}

function ErrorCard({ reply, accent }) {
  return (
    <div className={styles.card} style={{ '--accent': accent }}>
      <p className={styles.errorText}>{reply.content}</p>
    </div>
  )
}

export default function MessageBubble({ role, text, image, reply, accent, onQuickReply }) {
  const isUser = role === 'user'

  return (
    <div className={`${styles.row} ${isUser ? styles.rowUser : ''}`}>
      <div className={`${styles.bubble} ${isUser ? styles.user : styles.assistant}`}>
        {image && <img src={image} alt="Attached" className={styles.image} />}
        {text && <p className={styles.text}>{text}</p>}
        {reply?.type === 'text' && <p className={styles.text}>{reply.content}</p>}
        {reply?.type === 'runner' && (
          <CompareRunner kind={reply.kind} image={reply.image} text={reply.text} accent={accent} />
        )}
        {reply?.type === 'toxicity' && <ToxicityCard reply={reply} accent={accent} />}
        {reply?.type === 'diet' && <DietCard reply={reply} accent={accent} />}
        {reply?.type === 'error' && <ErrorCard reply={reply} accent={accent} />}

        {reply?.quickReplies && (
          <div className={styles.chips}>
            {reply.quickReplies.map((chip) => (
              <button
                key={chip}
                className={styles.chip}
                style={{ '--accent': accent }}
                onClick={() => onQuickReply?.(chip)}
              >
                {chip}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
