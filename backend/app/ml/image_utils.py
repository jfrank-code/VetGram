"""
Shared image-loading helper for the specialist models. `image_base64` can
arrive as either a real data URL (from a photo the user attached, read via
FileReader on the frontend) or a plain http(s) URL (from "Try a sample
photo", which points at a Wikimedia Commons image directly instead of
encoding it) — this handles both, instead of assuming it's always base64.
"""
import base64
import io

import requests
from PIL import Image

# Wikimedia actively rejects requests with a generic/default User-Agent
# (403 Forbidden) — see https://meta.wikimedia.org/wiki/User-Agent_policy.
# A descriptive one is required, not optional.
_HEADERS = {"User-Agent": "VetGram/1.0 (hackathon project; contact: set-your-email-here)"}


def decode_image(image_ref: str) -> Image.Image:
    if image_ref.startswith("http://") or image_ref.startswith("https://"):
        response = requests.get(image_ref, headers=_HEADERS, timeout=15)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")

    if image_ref.startswith("data:image"):
        image_ref = image_ref.split(",", 1)[1]

    raw = base64.b64decode(image_ref)
    return Image.open(io.BytesIO(raw)).convert("RGB")
