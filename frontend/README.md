# VetGram — Frontend

A landing page presenting the product, followed by a chatbot with four
switchable modes: breed identification, diet planning, skin screening, and
food safety. Connected to the VetGram FastAPI backend for real GPT-4o-mini
replies.

## Stack

- **React 18** — UI library
- **Vite** — dev server and bundler
- **CSS Modules** — scoped component styling with custom design tokens
- **lucide-react** — icon set
- **Google Fonts** — Fraunces (headings/logo), IBM Plex Sans (body), IBM
  Plex Mono (data readouts, model labels)

## Run it

```bash
npm install
cp .env.example .env   # only needed if the backend isn't on localhost:8000
npm run dev
```

Make sure the backend (`vetgram-backend`) is running on `http://localhost:8000`
(or whatever you set `VITE_API_URL` to) — this app has no offline/mock mode
anymore.

## Folder structure

```
frontend/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx                    # toggles Landing <-> ChatApp
    ├── styles/globals.css         # design tokens
    ├── services/
    │   └── api.js                 # fetch wrapper for POST /api/chat
    ├── data/
    │   ├── modes.js                # the 4 modes: id, label, icon, accent, prompts
    │   └── specialistExamples.js   # mocked "Specialist model" examples (ML models not built yet)
    └── components/
        ├── Landing/                  # pre-app presentation: hero, mode cards, CTA
        ├── ChatApp/                   # state: messages + history per mode, typing, API calls
        ├── ModeTabs/                  # mode switcher with icons
        ├── MessageBubble/             # renders text / diet / toxicity / runner / error + chips
        ├── CompareRunner/             # dual-panel: mocked specialist vs real GPT-4o-mini call
        ├── TypingIndicator/           # animated "assistant is thinking" dots
        └── Composer/                   # text input, real image attach, suggestion chips
```

## How each mode works

- **Breed ID** and **Skin Screening**: attaching a photo shows a `runner`
  reply — two independent panels, each with its own **Run** button.
  "Specialist model" is still mocked (cycles through canned examples — the
  real ML classifier is a later milestone). "GPT-4o-mini" calls the real
  backend with that photo and shows the actual model's answer, with a retry
  button if the request fails. Sending a photo-less follow-up question
  (e.g. "what temperament does that breed have?") goes straight to the
  backend as plain text instead of opening a new compare card. Both modes
  also offer "Try a sample photo" so the flow can be demoed without a real
  picture on hand.
- **Diet Expert** is a free-form conversation with the backend — GPT asks
  for species, weight, life stage, and activity level, then hands off to
  the backend to compute RER/MER with the real WSAVA/NRC formula once it
  has everything; the reply becomes a `diet` card.
- **Food Safety** sends the message (and/or photo) to the backend, which
  returns a per-item safe/unsafe/depends verdict for everything it
  recognizes; the reply becomes a `toxicity` card listing every item, not
  just the most dangerous one.

Each mode keeps a short text-only history (`historyByMode` in `ChatApp.jsx`)
so the backend has conversational context on follow-up messages.
