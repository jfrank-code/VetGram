import json
import logging

import openai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

from .config import (
    ALLOWED_ORIGIN_REGEX,
    ALLOWED_ORIGINS,
    CHAT_MAX_TOKENS,
    CHAT_TEMPERATURE,
    MAX_HISTORY_TURNS,
    MAX_IMAGE_BASE64_CHARS,
    MAX_MESSAGE_LENGTH,
    MODEL,
    OPENAI_API_KEY,
)
from .ml.breed_classifier import classify_breed
from .ml.skin_classifier import classify_skin
from .prompts import SYSTEM_PROMPTS
from .schemas import (
    CALCULATE_FEEDING_PLAN_TOOL,
    FOOD_SAFETY_JSON_SCHEMA,
    ChatRequest,
    ChatResponse,
    ClassifyRequest,
    ClassifyResponse,
    DietReply,
    TextReply,
    ToxicityItem,
    ToxicityReply,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vetgram")

app = FastAPI(title="VetGram API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=OPENAI_API_KEY)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---- Deterministic feeding-plan math ---------------------------------------
# RER/MER per WSAVA/NRC guidance. Kept as plain code (not GPT arithmetic) on
# purpose — this is the one place in the app where a wrong number could lead
# to real underfeeding/overfeeding advice.

_ACTIVITY_FACTORS = {
    "low": 1.3,
    "moderate": 1.6,
    "high": 1.9,
}
_GROWTH_FACTOR = 2.5  # puppy_kitten overrides activity_level


def calculate_feeding_plan(species: str, weight_kg: float, life_stage: str, activity_level: str) -> DietReply:
    if weight_kg <= 0 or weight_kg > 120:
        raise ValueError("weight_kg out of a plausible range for a dog or cat")

    rer = 70 * (weight_kg ** 0.75)
    factor = _GROWTH_FACTOR if life_stage == "puppy_kitten" else _ACTIVITY_FACTORS.get(activity_level, 1.6)
    mer = rer * factor

    return DietReply(
        species=species,
        weight_kg=weight_kg,
        life_stage=life_stage,
        activity_level=activity_level,
        rer_kcal=round(rer, 1),
        mer_kcal=round(mer, 1),
        explanation="",  # filled in after GPT explains the result
    )


# ---- Shared helpers ---------------------------------------------------------

def _validate_request(req: ChatRequest) -> None:
    if not req.message and not req.image_base64:
        raise HTTPException(status_code=400, detail="Send a message, an image, or both.")

    if req.message and len(req.message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Message is too long (max {MAX_MESSAGE_LENGTH} characters).",
        )

    if req.image_base64:
        is_data_url = req.image_base64.startswith("data:image/")
        is_remote_url = req.image_base64.startswith("http://") or req.image_base64.startswith("https://")
        if not (is_data_url or is_remote_url):
            raise HTTPException(
                status_code=400,
                detail="image_base64 must be a data:image/... URL or an http(s) image URL.",
            )
        if len(req.image_base64) > MAX_IMAGE_BASE64_CHARS:
            raise HTTPException(status_code=413, detail="Image is too large.")


def _build_messages(system_prompt: str, req: ChatRequest) -> list:
    messages = [{"role": "system", "content": system_prompt}]

    for turn in req.history[-MAX_HISTORY_TURNS:]:
        messages.append({"role": turn.role, "content": turn.content})

    if req.image_base64:
        content = [{"type": "text", "text": req.message or "Here's the photo."}]
        content.append({"type": "image_url", "image_url": {"url": req.image_base64}})
        messages.append({"role": "user", "content": content})
    else:
        messages.append({"role": "user", "content": req.message})

    return messages


def _call_openai(**kwargs):
    try:
        return client.chat.completions.create(model=MODEL, **kwargs)
    except openai.AuthenticationError as exc:
        logger.error("OpenAI auth error: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Server is misconfigured: the OpenAI API key was rejected. Check your .env.",
        ) from exc
    except openai.RateLimitError as exc:
        logger.warning("OpenAI rate limit: %s", exc)
        raise HTTPException(status_code=429, detail="Too many requests right now — try again shortly.") from exc
    except openai.APIConnectionError as exc:
        logger.error("OpenAI connection error: %s", exc)
        raise HTTPException(status_code=503, detail="Couldn't reach OpenAI — check your connection and retry.") from exc
    except openai.BadRequestError as exc:
        logger.warning("OpenAI bad request: %s", exc)
        raise HTTPException(status_code=400, detail=f"Request rejected by OpenAI: {exc}") from exc
    except openai.APIError as exc:
        logger.error("OpenAI API error: %s", exc)
        raise HTTPException(status_code=502, detail="OpenAI request failed. Try again in a moment.") from exc


# ---- Mode handlers -----------------------------------------------------------

def _handle_text_mode(mode: str, req: ChatRequest) -> TextReply:
    """Breed ID and Skin Screening — plain text in, plain text out."""
    messages = _build_messages(SYSTEM_PROMPTS[mode], req)
    completion = _call_openai(messages=messages, temperature=CHAT_TEMPERATURE, max_tokens=CHAT_MAX_TOKENS)
    return TextReply(content=completion.choices[0].message.content or "")


def _handle_food_mode(req: ChatRequest) -> "TextReply | ToxicityReply":
    messages = _build_messages(SYSTEM_PROMPTS["food"], req)
    completion = _call_openai(
        messages=messages,
        temperature=0.3,
        max_tokens=CHAT_MAX_TOKENS,
        response_format={"type": "json_schema", "json_schema": FOOD_SAFETY_JSON_SCHEMA},
    )
    raw = completion.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Food Safety returned non-JSON: %r", raw)
        return TextReply(content="Sorry, I had trouble reading that — could you try rephrasing?")

    if not data.get("on_topic") or not data.get("items"):
        return TextReply(content=data.get("message") or "Could you tell me which food you'd like me to check?")

    items = [ToxicityItem(**item) for item in data["items"]]
    return ToxicityReply(items=items)


def _handle_diet_mode(req: ChatRequest) -> "TextReply | DietReply":
    messages = _build_messages(SYSTEM_PROMPTS["diet"], req)
    completion = _call_openai(
        messages=messages,
        temperature=0.3,
        max_tokens=CHAT_MAX_TOKENS,
        tools=[CALCULATE_FEEDING_PLAN_TOOL],
        tool_choice="auto",
    )
    msg = completion.choices[0].message

    if not msg.tool_calls:
        return TextReply(content=msg.content or "")

    tool_call = msg.tool_calls[0]
    try:
        args = json.loads(tool_call.function.arguments)
        plan = calculate_feeding_plan(
            species=args["species"],
            weight_kg=float(args["weight_kg"]),
            life_stage=args["life_stage"],
            activity_level=args["activity_level"],
        )
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        logger.error("Diet Expert tool call had bad arguments: %s", exc)
        return TextReply(
            content="I didn't quite catch all the details — could you confirm your pet's species, weight in kg, life stage, and activity level?"
        )

    # Second round trip: hand the computed numbers back to the model so it
    # can explain them in its own words, instead of the backend inventing
    # copy. Keep it short and cheap.
    followup_messages = messages + [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(
                {"rer_kcal": plan.rer_kcal, "mer_kcal": plan.mer_kcal}
            ),
        },
    ]
    followup = _call_openai(messages=followup_messages, temperature=0.4, max_tokens=300)
    plan.explanation = followup.choices[0].message.content or ""
    return plan


# ---- Route --------------------------------------------------------------------

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if req.mode not in SYSTEM_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {req.mode}")

    _validate_request(req)

    if req.mode in ("breed", "skin"):
        reply = _handle_text_mode(req.mode, req)
    elif req.mode == "food":
        reply = _handle_food_mode(req)
    else:  # diet
        reply = _handle_diet_mode(req)

    return ChatResponse(reply=reply)


# ---- Specialist model routes (real ML, no GPT involved) -------------------
# Called directly by the "Specialist model" panel in CompareRunner, in
# parallel with /api/chat being called by the "GPT-4o-mini" panel — that's
# the actual side-by-side comparison the frontend shows.

@app.post("/api/classify/breed", response_model=ClassifyResponse)
def classify_breed_endpoint(req: ClassifyRequest):
    try:
        result = classify_breed(req.image_base64)
    except Exception as exc:  # noqa: BLE001 — surface it, don't hide it
        logger.error("Breed classifier failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Specialist model failed: {exc}") from exc
    return ClassifyResponse(**result)


@app.post("/api/classify/skin", response_model=ClassifyResponse)
def classify_skin_endpoint(req: ClassifyRequest):
    try:
        result = classify_skin(req.image_base64)
    except Exception as exc:  # noqa: BLE001
        logger.error("Skin classifier failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Specialist model failed: {exc}") from exc
    return ClassifyResponse(**result)