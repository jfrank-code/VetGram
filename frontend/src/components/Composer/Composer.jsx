import { useRef, useState } from 'react'
import { Paperclip, Send, X } from 'lucide-react'
import styles from './Composer.module.css'

export default function Composer({ placeholder, accent, suggestions, onSend }) {
  const [text, setText] = useState('')
  const [image, setImage] = useState(null)
  const fileInputRef = useRef(null)

  function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setImage(reader.result)
    reader.readAsDataURL(file)
    e.target.value = ''
  }

  function submit(payload) {
    if (!payload.text?.trim() && !payload.image) return
    onSend(payload)
    setText('')
    setImage(null)
  }

  function handleSubmit(e) {
    e.preventDefault()
    submit({ text: text.trim(), image })
  }

  return (
    <div className={styles.wrap} style={{ '--accent': accent }}>
      {suggestions?.length > 0 && (
        <div className={styles.suggestions}>
          {suggestions.map((s) => (
            <button key={s} type="button" className={styles.suggestion} onClick={() => submit({ text: s })}>
              {s}
            </button>
          ))}
        </div>
      )}

      <form className={styles.composer} onSubmit={handleSubmit}>
        {image && (
          <div className={styles.preview}>
            <img src={image} alt="Selected" />
            <button type="button" className={styles.removeBtn} onClick={() => setImage(null)}>
              <X size={13} />
            </button>
          </div>
        )}

        <div className={styles.row}>
          <button type="button" className={styles.attachBtn} onClick={() => fileInputRef.current?.click()}>
            <Paperclip size={18} />
          </button>
          <input ref={fileInputRef} type="file" accept="image/*" onChange={handleFile} className={styles.hiddenInput} />

          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={placeholder}
            className={styles.textInput}
          />

          <button type="submit" className={styles.sendBtn} disabled={!text.trim() && !image}>
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  )
}
