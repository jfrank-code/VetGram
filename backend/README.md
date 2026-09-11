# VetGram — Backend

FastAPI backend for VetGram's 4 chat modes, calling GPT-4o-mini through a
single endpoint. Two of the modes (Food Safety, Diet Expert) are wired for
structured, deterministic answers instead of trusting free-form GPT text —
see "How each mode answers" below.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your real OpenAI API key
uvicorn app.main:app --reload --port 8000
```

Check it's alive: `GET http://localhost:8000/health` → `{"status": "ok"}`

`.env` is already in `.gitignore` — your key never gets committed. Only
`.env.example` (a placeholder) is tracked.

## The one endpoint

`POST /api/chat`

```json
{
  "mode": "breed",           // "breed" | "diet" | "skin" | "food"
  "message": "What breed is this?",   // optional if an image is sent
  "image_base64": "data:image/png;base64,....",  // optional, data-URL format
  "history": [                 // optional, prior turns for context
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

Response — the `reply.type` tells the frontend which card to render:

```json
{ "reply": { "type": "text", "content": "This looks like a Labrador Retriever mix..." } }
{ "reply": { "type": "toxicity", "items": [{ "name": "grapes", "status": "unsafe", "note": "..." }] } }
{ "reply": { "type": "diet", "species": "dog", "weight_kg": 12, "life_stage": "adult", "activity_level": "moderate", "rer_kcal": 396.5, "mer_kcal": 634.4, "explanation": "..." } }
```

## How each mode answers

- **Breed ID / Skin Screening** — plain text. The model just talks, the
  backend passes its reply straight through as `{"type": "text"}`.
- **Food Safety** — forced into strict JSON (OpenAI structured outputs, see
  `FOOD_SAFETY_JSON_SCHEMA` in `schemas.py`) so every food item in the
  message/photo gets its own `safe` / `unsafe` / `depends` verdict with a
  reason, instead of free text that's hard to parse reliably. If the
  message isn't about food safety, the backend returns `{"type": "text"}`
  with the model's redirect/clarifying question instead.
- **Diet Expert** — GPT never does the arithmetic. It asks for species,
  weight, life stage, and activity level conversationally (plain text
  replies while it's still gathering info), then calls a
  `calculate_feeding_plan` tool once it has everything. The **backend**
  computes RER/MER with the actual WSAVA/NRC formula
  (`calculate_feeding_plan()` in `main.py`) — GPT only explains the result
  afterward, in its own words. This is safer than letting a language model
  do the numbers-sensitive part.

## Error handling

OpenAI errors are caught and mapped to sensible HTTP status codes instead
of leaking raw exceptions: bad/missing key → 500 with a clear "check your
.env" message, rate limits → 429, connectivity issues → 503, malformed
requests → 400. Requests are also validated before they ever reach OpenAI:
message length cap, image size cap, image must be a `data:image/...` URL.

## Files

```
app/
├── main.py       # FastAPI app, /api/chat, /api/classify/*, diet math, error handling
├── prompts.py    # the 4 system prompts
├── schemas.py    # request/response models + the JSON schema and tool definitions
├── config.py     # env vars: API key, model, CORS origins, guardrail limits
└── ml/
    ├── breed_classifier.py   # real pretrained model (Hugging Face), no training needed
    ├── skin_classifier.py    # real pretrained model (Hugging Face), no training needed
    └── image_utils.py        # shared decoder: handles both data URLs and plain http(s) URLs
```

## The specialist models (real ML, separate from GPT)

Two more endpoints, called directly by the "Specialist model" panel — no
GPT involved on this side of the comparison:

`POST /api/classify/breed` and `POST /api/classify/skin`

```json
{ "image_base64": "data:image/png;base64,...." }
```

`image_base64` also accepts a plain `http(s)://` image URL (that's what
"Try a sample photo" sends) — `image_utils.py` handles both.

```json
{ "label": "Labrador Retriever mix", "confidence": 94.2 }
```

Both panels are now real, pretrained models — neither needs training:

- **Breed ID**: `deyakovleva/vit-base-oxford-iiit-pets` on Hugging Face
  (~93.5% accuracy, Oxford-IIIT Pet Dataset's 37 breeds). Downloads once
  (~350MB, cached after).
- **Skin Screening**: `ikchain/vet-dermatology-canine` on Hugging Face —
  EfficientNetV2-S fine-tuned for canine skin lesions, 94.0% accuracy on a
  433-image held-out test. 6 classes: demodicosis, dermatitis, fungal
  infection, healthy, hypersensitivity/allergic dermatitis, ringworm.
  Downloads once (~201MB, cached after). Verified directly on
  huggingface.co before adding it — it's a small, low-visibility model
  from another hackathon project ("Howl Vision"), so it didn't turn up in
  general search and had to be confirmed by opening the exact page and
  file listing.

  Two things worth knowing before you lean on this in a demo: the
  checkpoint is a raw PyTorch pickle (not `safetensors`) — Hugging Face
  itself flags this as a minor trust consideration, low risk here given
  it's a single-contributor hackathon upload, but worth a one-line
  mention rather than pretending it doesn't apply. And the 6-class label
  order in `skin_classifier.py` is inferred from the model card's listed
  order (it matches a standard alphabetical class-folder sort), not
  independently confirmed — run one known-healthy photo through it once
  and check it actually says "Healthy" before trusting it in front of
  judges.

**Honest limitation from development:** both were written and
logic-tested in a sandboxed environment with no real network access to
Hugging Face (requests either got blocked outright or timed out
mid-download), so the actual end-to-end download could not be completed
here — only the code paths, architecture, and error handling were
verified locally. The breed model has already been confirmed working on
your machine; test the skin one the same way as the first thing you do
with this milestone.

## Connecting the frontend

Already wired — see `src/services/api.js` in the frontend repo
(`sendChatMessage`, `classifyBreed`, `classifySkin`). Set `VITE_API_URL`
in the frontend's `.env` if the backend isn't on `http://localhost:8000`.
