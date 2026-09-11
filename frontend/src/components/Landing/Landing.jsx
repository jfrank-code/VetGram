import { PawPrint, Utensils, Stethoscope, ShieldAlert, ArrowRight } from 'lucide-react'
import { modes } from '../../data/modes.js'
import styles from './Landing.module.css'

const ICONS = { PawPrint, Utensils, Stethoscope, ShieldAlert }

const CARD_COPY = {
  breed: 'Photo in, species and breed out — checked against a specialist model and GPT side by side.',
  diet: 'A short conversation turns weight and activity into an exact daily gram dose, using real WSAVA/NRC formulas.',
  skin: 'Screens for 6 trained skin conditions with a real fine-tuned model, while GPT offers a second, broader opinion.',
  food: "Ask about an ingredient or send a photo of the plate — checked against ASPCA's known-hazards list.",
}

const BADGES = ['Oxford-IIIT Pet Dataset', 'WSAVA · NRC standards', 'ASPCA hazard list', 'GPT-4o-mini']

export default function Landing({ onLaunch }) {
  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        <div className={styles.pill}>Veterinary-grade AI, in one chat</div>

        <h1 className={styles.headline}>
          Know your pet <span className={styles.accentText}>before</span> something goes wrong.
        </h1>

        <p className={styles.lede}>
          VetGram is a chatbot with four expert modes — breed identification, diet planning,
          skin screening, and food safety — each grounded in real veterinary data, not guesses.
        </p>

        <button className={styles.cta} onClick={onLaunch}>
          Launch VetGram <ArrowRight size={16} />
        </button>

        <div className={styles.badges}>
          {BADGES.map((b) => (
            <span key={b} className={styles.badge}>
              {b}
            </span>
          ))}
        </div>

        <div className={styles.grid}>
          {modes.map((mode) => {
            const Icon = ICONS[mode.icon]
            return (
              <button
                key={mode.id}
                className={styles.card}
                style={{ '--accent': mode.accent }}
                onClick={onLaunch}
              >
                <div className={styles.cardIcon}>
                  <Icon size={18} />
                </div>
                <div className={styles.cardLabel}>{mode.label}</div>
                <p className={styles.cardCopy}>{CARD_COPY[mode.id]}</p>
              </button>
            )
          })}
        </div>

        <p className={styles.footnote}>
          Built for AnimalHack 2026 — screening tools only, never a replacement for a real
          veterinary exam.
        </p>
      </div>
    </div>
  )
}
