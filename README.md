# VetGram

**Know your pet before something goes wrong.**

VetGram is a chatbot for pet owners with four expert modes — Breed ID,
Diet Expert, Skin Screening, and Food Safety — each grounded in real
veterinary data instead of a single AI's unverified guess.

---

## The problem

Pet owners constantly face a critical decision gap: minor symptoms, daily nutrition choices, and sudden health doubts trigger immediate anxiety, yet lack an accessible, trustworthy place for quick validation. When a dog eats something unusual or shows mild skin redness, owners are forced to choose between an expensive, non-urgent vet visit or drowning in generic, conflicting, and unverified search engine results.

VetGram bridges this gap by transforming uncertain moments into informed actions. Powered by validated reference databases—such as WSAVA/NRC nutrition guidelines, ASPCA toxicity data, and specialized veterinary datasets—VetGram provides immediate, evidence-based triage. It isn't a replacement for a veterinarian; it is a reliable first filter that helps owners distinguish between a simple "monitor at home" situation and an urgent clinic visit, accessible instantly through any web browser.

## The solution

VetGram is that first, well-informed pass — never a replacement for a
vet, but somewhere to go before or between vet visits, with four modes
that each target one piece of the problem above:

| Mode | What it solves |
|---|---|
| 🍽️ **Food Safety** | Catches the "wait, can they even eat that?" mistake before it becomes a poisoning emergency — checks against real veterinary toxicology guidance (ASPCA Animal Poison Control), item by item, even for a whole plate at once. |
| 🥣 **Diet Expert** | Replaces guesswork ("just fill the bowl") with an actual WSAVA/NRC-based daily calorie target, computed with a real formula — plus real guidance on *what* to feed by life stage and breed size. |
| 🩺 **Skin Screening** | A same-minute, non-diagnostic first opinion on a skin concern, checked against a model trained specifically on canine skin lesions — enough to tell "monitor this" from "this needs a vet today." |
| 🐾 **Breed ID** | Identifies likely breed/mix from a photo — useful for the huge share of shelter and mixed-breed pets whose owners simply don't know — so the health, exercise, and feeding considerations tied to that breed are actually knowable. |

### Two kinds of AI, checked against each other

The part that makes this more than "ask a chatbot": Breed ID and Skin
Screening each run **two different, independent models on the same photo,
side by side** — the user sees both answers, not just one:

1. **A specialist machine learning model** — an actual model trained for
   that specific task, not a general-purpose AI. Breed ID uses a Vision
   Transformer fine-tuned on the Oxford-IIIT Pet Dataset (37 breed
   classes); Skin Screening uses an EfficientNetV2 model fine-tuned
   specifically on canine skin lesion photos (6 condition classes). These
   run locally on the backend and return a label with a real confidence
   score — no GPT involved on this side.
2. **GPT-4o-mini**, looking at the same photo independently, with a
   system prompt scoped tightly to that one task, and asked to reason
   through it in plain language (e.g. for skin, naming 2-4 plausible
   conditions instead of one guess).

Neither one is presented as "the" answer. Showing them side by side is
the point: a specialist model is narrow but precise within what it was
trained on, and can be confidently wrong outside that (e.g. a breed not
in its 37 trained classes); GPT is broader and can reason in words, but
isn't a trained medical classifier either. Comparing them is more honest
than picking one and hiding the disagreement.

The other two modes (Diet Expert, Food Safety) use GPT-4o-mini alone, but
constrained the same way this project treats every numbers- or
safety-sensitive answer: GPT never invents the calorie math (a real
WSAVA/NRC formula in the backend computes it, GPT only explains the
result), and Food Safety's output is forced into a structured per-item
format instead of free text, so nothing gets glossed over in a multi-item
question.

## Architecture

```
┌─────────────────────────┐         ┌──────────────────────────────┐
│   Frontend (React+Vite) │  HTTPS  │   Backend (FastAPI)           │
│                          │ ──────► │                                │
│  Landing → 4-mode chat   │         │  POST /api/chat                │
│  UI, compare-panel view  │ ◄────── │    → GPT-4o-mini (per-mode     │
└─────────────────────────┘         │      system prompt, structured │
                                     │      output for Food Safety,   │
                                     │      tool-calling for Diet)    │
                                     │                                 │
                                     │  POST /api/classify/breed      │
                                     │    → ViT fine-tuned on          │
                                     │      Oxford-IIIT Pet (37        │
                                     │      breeds)                    │
                                     │                                 │
                                     │  POST /api/classify/skin       │
                                     │    → EfficientNetV2 fine-tuned  │
                                     │      on canine skin lesions     │
                                     │      (6 conditions)             │
                                     └──────────────────────────────┘
```

- **Frontend**: React + Vite, plain CSS Modules, no UI framework. A
  landing page presents the product, then a single-page chat app switches
  between the 4 modes. Each mode keeps its own short conversation history
  so follow-up questions have context.
- **Backend**: FastAPI, one main endpoint (`/api/chat`) that routes to a
  per-mode system prompt, plus two ML endpoints (`/api/classify/breed`,
  `/api/classify/skin`) that run real pretrained/fine-tuned models
  locally — no GPT involved on that side of the comparison.
- **Two "brains" per visual mode**: Breed ID and Skin Screening both show
  a specialist-model result and a GPT-4o-mini result side by side, so a
  wrong or uncertain answer from either one is visible rather than
  hidden behind a single confident-sounding response.
- **Numbers-sensitive logic stays in code, not in the model**: Diet
  Expert's calorie math (RER/MER, WSAVA/NRC formulas) is computed by the
  backend, not by GPT — the model gathers the inputs conversationally and
  explains the result afterward, but never does the arithmetic itself.

## Tech stack

| | |
|---|---|
| Frontend | React 18, Vite, CSS Modules, lucide-react |
| Backend | FastAPI, Pydantic, Uvicorn |
| AI | OpenAI GPT-4o-mini (chat, vision, structured outputs, tool calling) |
| Specialist models | ViT (`deyakovleva/vit-base-oxford-iiit-pets`), EfficientNetV2-S (`ikchain/vet-dermatology-canine`) via 🤗 Transformers/timm |
| Data sources | Oxford-IIIT Pet Dataset, WSAVA & NRC nutrition guidelines, ASPCA Animal Poison Control hazard list |
| Deployment | Railway (two services: `backend/`, `frontend/`) |

## Repo structure

```
vetgram/
├── backend/     # FastAPI app — see backend/README.md for the full API,
│                #   prompt design, and ML model details
└── frontend/    # React + Vite app — see frontend/README.md for the
                 #   component structure and how each mode works
```

## Running it locally

Both services need to run at the same time — see each folder's own
README for the full details (env vars, dependencies, model downloads).
The short version:

```bash
# terminal 1 — backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # paste your OpenAI API key
uvicorn app.main:app --reload --port 8000

# terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Then open the frontend's local URL (Vite prints it, usually
`http://localhost:5173`).

## Deployment

Deployed as two separate Railway services from this same repo (Root
Directory set to `backend` and `frontend` respectively). See
`backend/Procfile` and `frontend/Procfile`.