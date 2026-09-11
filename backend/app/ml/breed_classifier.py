"""
Breed classifier — the real "Specialist model" for Breed ID.

Loads an already fine-tuned model from Hugging Face
(deyakovleva/vit-base-oxford-iiit-pets — a ViT fine-tuned on the
Oxford-IIIT Pet Dataset's 37 breeds, ~93.5% accuracy). No training
required, this is a ready model, not a dataset you train yourself.

IMPORTANT — read before assuming this "just works":
This was written and syntax-checked in a sandboxed dev environment whose
network access is restricted to a short allowlist (github, pypi, a few
others) that does NOT include huggingface.co. That means the actual
download-and-run step could not be executed or verified end to end during
development. The code follows the standard `transformers` API correctly,
but the first time YOU run this on a machine with normal internet access,
watch the first request closely:
  - It will download ~350MB of model weights to ~/.cache/huggingface the
    first time `classify_breed()` is called (lazy-loaded, not at import
    time) — that request will be slow. Every request after that is fast,
    since it's cached locally.
  - If `deyakovleva/vit-base-oxford-iiit-pets` has been removed or renamed
    since this was written, from_pretrained() will raise a clear 404-style
    error — swap MODEL_ID for an equivalent breed-classification model if
    that happens.
"""
import re

import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

from .image_utils import decode_image

MODEL_ID = "deyakovleva/vit-base-oxford-iiit-pets"

_model = None
_processor = None


def _load():
    global _model, _processor
    if _model is None:
        _processor = AutoImageProcessor.from_pretrained(MODEL_ID)
        _model = AutoModelForImageClassification.from_pretrained(MODEL_ID)
        _model.eval()
    return _model, _processor


def _prettify_label(label: str) -> str:
    # Labels look like "yorkshire_terrier" — turn into "Yorkshire Terrier".
    return re.sub(r"[_\-]+", " ", label).title()


def classify_breed(image_base64: str) -> dict:
    """Returns {"label": str, "confidence": float 0-100}."""
    model, processor = _load()
    image = decode_image(image_base64)

    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.nn.functional.softmax(logits, dim=-1)[0]
    top_prob, top_idx = torch.max(probs, dim=0)

    label = model.config.id2label[top_idx.item()]
    return {"label": _prettify_label(label), "confidence": round(top_prob.item() * 100, 1)}
