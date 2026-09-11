import { useState } from 'react'
import { Play, Cpu, Sparkles, RotateCcw } from 'lucide-react'
import { classifyBreed, classifySkin } from '../../services/api.js'
import { sendChatMessage } from '../../services/api.js'
import styles from './CompareRunner.module.css'

const SKIN_FOOTNOTE =
  'The specialist model only recognizes 6 trained conditions (demodicosis, dermatitis, fungal infection, healthy, allergic dermatitis, ringworm). GPT-4o-mini can comment more broadly, but is not clinically validated.'

function Panel({ label, icon, accent, status, value, meta, onRun }) {
  return (
    <div className={styles.panel} style={{ '--accent': accent }}>
      <div className={styles.panelHead}>
        {icon}
        <span>{label}</span>
      </div>

      {status === 'idle' && (
        <button className={styles.runBtn} onClick={onRun}>
          <Play size={13} /> Run
        </button>
      )}

      {status === 'loading' && (
        <div className={styles.loading}>
          <span className={styles.spinner} />
          Analyzing…
        </div>
      )}

      {status === 'done' && (
        <div className={styles.result}>
          <div className={styles.resultValue}>{value}</div>
          {meta && <div className={styles.resultMeta}>{meta}</div>}
        </div>
      )}

      {status === 'error' && (
        <div className={styles.result}>
          <div className={styles.resultMeta}>{value}</div>
          <button className={styles.runBtn} onClick={onRun}>
            <RotateCcw size={13} /> Retry
          </button>
        </div>
      )}
    </div>
  )
}

export default function CompareRunner({ kind, image, text, accent }) {
  const [specialist, setSpecialist] = useState({ status: 'idle' })
  const [gpt, setGpt] = useState({ status: 'idle' })

  async function runSpecialist() {
    setSpecialist({ status: 'loading' })
    try {
      const classifyFn = kind === 'breed' ? classifyBreed : classifySkin
      const result = await classifyFn(image)
      setSpecialist({ status: 'done', value: result.label, meta: `${result.confidence}% confidence` })
    } catch (err) {
      setSpecialist({ status: 'error', value: err.message || 'Specialist model failed.' })
    }
  }

  async function runGpt() {
    setGpt({ status: 'loading' })
    try {
      const reply = await sendChatMessage(kind, { text, image })
      const content = reply?.type === 'text' ? reply.content : 'Unexpected response from GPT.'
      setGpt({ status: 'done', value: content, meta: 'GPT-4o-mini — general vision model' })
    } catch (err) {
      setGpt({ status: 'error', value: err.message || 'GPT request failed.' })
    }
  }

  const bothDone = specialist.status === 'done' && gpt.status === 'done'

  return (
    <div className={styles.wrap} style={{ '--accent': accent }}>
      <div className={styles.grid}>
        <Panel
          label="Specialist model"
          icon={<Cpu size={13} />}
          accent={accent}
          status={specialist.status}
          value={specialist.value}
          meta={specialist.meta}
          onRun={runSpecialist}
        />
        <Panel
          label="GPT-4o-mini"
          icon={<Sparkles size={13} />}
          accent={accent}
          status={gpt.status}
          value={gpt.value}
          meta={gpt.meta}
          onRun={runGpt}
        />
      </div>

      {bothDone && kind === 'skin' && <p className={styles.footnote}>{SKIN_FOOTNOTE}</p>}
    </div>
  )
}
