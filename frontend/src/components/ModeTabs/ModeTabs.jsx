import { PawPrint, Utensils, Stethoscope, ShieldAlert } from 'lucide-react'
import { modes } from '../../data/modes.js'
import styles from './ModeTabs.module.css'

const ICONS = { PawPrint, Utensils, Stethoscope, ShieldAlert }

export default function ModeTabs({ activeMode, onChange }) {
  return (
    <div className={styles.tabs}>
      {modes.map((mode) => {
        const Icon = ICONS[mode.icon]
        return (
          <button
            key={mode.id}
            className={`${styles.tab} ${activeMode === mode.id ? styles.active : ''}`}
            style={{ '--accent': mode.accent }}
            onClick={() => onChange(mode.id)}
          >
            <Icon size={14} />
            <span>{mode.label}</span>
          </button>
        )
      })}
    </div>
  )
}
