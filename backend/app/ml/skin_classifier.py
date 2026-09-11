"""
Skin condition classifier — the real "Specialist model" for Skin
Screening.

Loads a real, already fine-tuned model from Hugging Face:
ikchain/vet-dermatology-canine — EfficientNetV2-S fine-tuned specifically
for canine skin lesion classification (6 classes), 94.0% accuracy on a
433-image held-out test set (91.5%-95.8% Wilson 95% CI). Built for the
"Gemma 4 Good Hackathon" (project "Howl Vision").

VERIFIED DIRECTLY on huggingface.co before use, including the file
listing (the 201MB vet_dermatology.pt checkpoint is really there) — this
is a small, low-visibility model from another hackathon that didn't
surface in general search, so it was confirmed by opening the exact page,
not assumed. This replaces the earlier plan of training a classifier from
scratch — no training needed for this one.

SECURITY NOTE, said plainly rather than hidden: this checkpoint is a raw
PyTorch pickle file, not the safer `safetensors` format — Hugging Face's
own file browser flags this on the model's page. Loading a pickle can, in
principle, run arbitrary code if the source were malicious. This is a
single-contributor hackathon upload; the risk reads as low, but it isn't
zero. Worth a one-line mention in your own presentation rather than
pretending it doesn't apply.

CLASS ORDER: the model card lists 6 classes in the order below, which
matches a case-insensitive alphabetical sort of the class names — the
same order torchvision's ImageFolder assigns during training, and the
best evidence available (the original training code isn't published).
This was NOT independently re-verified against ground truth. Before
trusting this in a live demo: run one clearly healthy photo through it
once and confirm it actually comes back "Healthy" — if it doesn't, the
indices are shifted and this list needs reordering.
"""
import torch
import timm
from huggingface_hub import hf_hub_download
from torchvision import transforms

from .image_utils import decode_image

MODEL_ID = "ikchain/vet-dermatology-canine"
MODEL_FILENAME = "vet_dermatology.pt"
TIMM_ARCH = "tf_efficientnetv2_s.in21k_ft_in1k"

CLASSES = [
    "Demodicosis",
    "Dermatitis",
    "Fungal infection",
    "Healthy",
    "Hypersensitivity / allergic dermatitis",
    "Ringworm",
]

_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((384, 384)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

_model = None


def _load():
    global _model
    if _model is None:
        weights_path = hf_hub_download(repo_id=MODEL_ID, filename=MODEL_FILENAME)
        model = timm.create_model(TIMM_ARCH, pretrained=False, num_classes=len(CLASSES))
        # weights_only=False matches what the model card itself specifies —
        # required because the checkpoint is a plain dict wrapping the state
        # dict, not a raw safetensors weights file.
        checkpoint = torch.load(weights_path, map_location="cpu", weights_only=False)
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()
        _model = model
    return _model


def classify_skin(image_base64: str) -> dict:
    """Returns {"label": str, "confidence": float 0-100}."""
    model = _load()
    image = decode_image(image_base64)
    tensor = _TRANSFORM(image).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor)
    probs = torch.nn.functional.softmax(logits, dim=-1)[0]
    top_prob, top_idx = torch.max(probs, dim=0)

    return {"label": CLASSES[top_idx.item()], "confidence": round(top_prob.item() * 100, 1)}
