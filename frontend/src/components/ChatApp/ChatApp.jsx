import { useEffect, useRef, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import ModeTabs from '../ModeTabs/ModeTabs.jsx'
import MessageBubble from '../MessageBubble/MessageBubble.jsx'
import TypingIndicator from '../TypingIndicator/TypingIndicator.jsx'
import Composer from '../Composer/Composer.jsx'
import { modes } from '../../data/modes.js'
import { getBreedSampleImage, getSkinSampleImage } from '../../data/specialistExamples.js'
import { sendChatMessage } from '../../services/api.js'
import styles from './ChatApp.module.css'

let idCounter = 0
const nextId = () => `m${idCounter++}`

// Modes where an attached image is analyzed via the two-panel
// specialist-vs-GPT compare card, instead of a single text reply.
const COMPARE_MODES = new Set(['breed', 'skin'])

function introMessage(mode) {
  return {
    id: nextId(),
    role: 'assistant',
    reply: {
      type: 'text',
      content: mode.intro,
      quickReplies: mode.introQuickReplies?.length ? mode.introQuickReplies : undefined,
    },
  }
}

// Turns a backend reply into a short plain-text summary, so the next
// request in this mode can send it back as conversation history.
function toHistoryContent(reply) {
  if (!reply) return ''
  if (reply.type === 'text') return reply.content
  if (reply.type === 'diet') return reply.explanation || `Daily target: ${reply.mer_kcal} kcal (MER).`
  if (reply.type === 'toxicity') {
    return reply.items.map((i) => `${i.name}: ${i.status} — ${i.note}`).join(' ')
  }
  return ''
}

function sampleForMode(modeId, index) {
  return modeId === 'breed' ? getBreedSampleImage(index) : getSkinSampleImage(index)
}

export default function ChatApp({ onBack }) {
  const [activeMode, setActiveMode] = useState(modes[0].id)
  const [messagesByMode, setMessagesByMode] = useState(() =>
    Object.fromEntries(modes.map((m) => [m.id, [introMessage(m)]])),
  )
  const [historyByMode, setHistoryByMode] = useState(() => Object.fromEntries(modes.map((m) => [m.id, []])))
  const [runnerCursorByMode, setRunnerCursorByMode] = useState(() => Object.fromEntries(modes.map((m) => [m.id, 0])))
  const [typingByMode, setTypingByMode] = useState(() => Object.fromEntries(modes.map((m) => [m.id, false])))

  // Every mode's thread stays mounted at all times (just hidden when not
  // active) so switching tabs never unmounts a CompareRunner mid-result —
  // that unmount was what reset already-fetched Run results back to idle.
  const threadRefs = useRef({})

  const mode = modes.find((m) => m.id === activeMode)

  useEffect(() => {
    const el = threadRefs.current[activeMode]
    el?.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  }, [messagesByMode[activeMode], typingByMode[activeMode], activeMode])

  function pushMessage(modeId, msg) {
    setMessagesByMode((prev) => ({ ...prev, [modeId]: [...prev[modeId], msg] }))
  }

  function appendHistory(modeId, userText, assistantContent) {
    setHistoryByMode((prev) => ({
      ...prev,
      [modeId]: [
        ...prev[modeId],
        ...(userText ? [{ role: 'user', content: userText }] : []),
        ...(assistantContent ? [{ role: 'assistant', content: assistantContent }] : []),
      ],
    }))
  }

  function handleQuickReply(value) {
    if (value === 'Try a sample photo') {
      const index = runnerCursorByMode[activeMode]
      handleSend({ image: sampleForMode(activeMode, index) })
    } else {
      handleSend({ text: value })
    }
  }

  async function handleSend({ text, image }) {
    const modeId = activeMode
    pushMessage(modeId, { id: nextId(), role: 'user', text, image })

    // Breed ID / Skin Screening with a photo: show the compare card right
    // away — each panel (specialist / GPT) fetches on its own when the
    // user hits "Run", so there's no need for a typing indicator here.
    if (COMPARE_MODES.has(modeId) && image) {
      // Cursor only matters for cycling through "Try a sample photo" images
      // (handleQuickReply below) — CompareRunner itself no longer needs an
      // index, both panels now run against the actual image sent.
      setRunnerCursorByMode((prev) => ({ ...prev, [modeId]: prev[modeId] + 1 }))
      pushMessage(modeId, {
        id: nextId(),
        role: 'assistant',
        reply: { type: 'runner', kind: modeId, image, text },
      })
      return
    }

    setTypingByMode((prev) => ({ ...prev, [modeId]: true }))
    try {
      const reply = await sendChatMessage(modeId, { text, image, history: historyByMode[modeId] })
      pushMessage(modeId, { id: nextId(), role: 'assistant', reply })
      appendHistory(modeId, text, toHistoryContent(reply))
    } catch (err) {
      pushMessage(modeId, {
        id: nextId(),
        role: 'assistant',
        reply: { type: 'error', content: err.message || 'Something went wrong — try again.' },
      })
    } finally {
      setTypingByMode((prev) => ({ ...prev, [modeId]: false }))
    }
  }

  return (
    <div className={styles.app}>
      <div className={styles.topbar}>
        <div className={styles.topbarTop}>
          <button className={styles.backBtn} onClick={onBack}>
            <ArrowLeft size={15} />
          </button>
          <span className={styles.logo}>VetGram</span>
        </div>
        <ModeTabs activeMode={activeMode} onChange={setActiveMode} />
      </div>

      <div className={styles.threadContainer}>
        {modes.map((m) => (
          <div
            key={m.id}
            ref={(el) => (threadRefs.current[m.id] = el)}
            className={styles.thread}
            style={{ display: activeMode === m.id ? 'block' : 'none' }}
          >
            {messagesByMode[m.id].map((msg) => (
              <MessageBubble key={msg.id} {...msg} accent={m.accent} onQuickReply={handleQuickReply} />
            ))}
            {typingByMode[m.id] && <TypingIndicator accent={m.accent} />}
          </div>
        ))}
      </div>

      <Composer
        placeholder={mode.placeholder}
        accent={mode.accent}
        suggestions={mode.suggestions}
        onSend={handleSend}
      />
    </div>
  )
}