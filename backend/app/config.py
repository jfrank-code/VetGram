import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
    )

# Model + generation settings — centralized here so they're easy to tune
# without hunting through main.py.
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.4"))
CHAT_MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "650"))

# CORS — comma-separated list via env var for deploys; sane localhost
# defaults for Vite dev (5173) and `vite preview` (4173) out of the box.
_default_origins = (
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:4173,http://127.0.0.1:4173"
)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

# Belt-and-suspenders for local dev: Vite auto-increments the port (5174,
# 5175...) if 5173 is already taken by another project, which would
# otherwise silently fail CORS (the browser preflight gets a real 400,
# not just a console warning) until someone notices and edits the list
# above by hand. This regex allows ANY localhost/127.0.0.1 port in
# addition to the explicit list — set ALLOWED_ORIGIN_REGEX="" to disable
# it for a production deploy.
ALLOWED_ORIGIN_REGEX = os.getenv(
    "ALLOWED_ORIGIN_REGEX", r"http://(localhost|127\.0\.0\.1):\d+"
) or None

# Basic input guardrails — keep requests small and cheap, and fail fast
# with a clear error instead of a confusing OpenAI-side rejection.
MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_TURNS = 16  # most recent turns kept; older ones are dropped
MAX_IMAGE_BASE64_CHARS = 8_000_000  # ~6 MB of actual image data