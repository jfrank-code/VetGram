// Thin wrapper around the VetGram backend's single /api/chat endpoint.
// Every mode (breed, diet, skin, food) goes through this same function —
// the backend decides what shape of reply to send back.

const rawUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_URL = rawUrl.replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// history: array of { role: 'user' | 'assistant', content: string }
export async function sendChatMessage(mode, { text, image, history = [] } = {}) {
  let response
  try {
    response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode,
        message: text || null,
        image_base64: image || null,
        history,
      }),
    })
  } catch (err) {
    throw new ApiError("Couldn't reach the VetGram backend — is it running?", 0)
  }

  let data
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    throw new ApiError(data?.detail || `Request failed (${response.status})`, response.status)
  }

  return data.reply
}

// The two specialist-model endpoints — real ML, no GPT involved. Called by
// CompareRunner's "Specialist model" panel, in parallel with sendChatMessage
// being called by the "GPT-4o-mini" panel.
async function classify(path, image) {
  let response
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_base64: image }),
    })
  } catch {
    throw new ApiError("Couldn't reach the VetGram backend — is it running?", 0)
  }

  let data
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    throw new ApiError(data?.detail || `Request failed (${response.status})`, response.status)
  }

  return data // { label, confidence }
}

export function classifyBreed(image) {
  return classify('/api/classify/breed', image)
}

export function classifySkin(image) {
  return classify('/api/classify/skin', image)
}
