from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field

Mode = Literal["breed", "diet", "skin", "food"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    mode: Mode
    message: Optional[str] = None
    # Data URL, e.g. "data:image/png;base64,...." — same format the
    # frontend already produces via FileReader.
    image_base64: Optional[str] = None
    history: List[ChatMessage] = []


# ---- Reply shapes ---------------------------------------------------------
# The frontend switches on `type` to decide which card to render. Breed ID
# and Skin Screening always reply with plain text (the model just talks).
# Food Safety and Diet Expert can escalate to a structured card once the
# model has enough to give a real answer — until then they also reply with
# plain text (a clarifying question, or an off-topic redirect).

class TextReply(BaseModel):
    type: Literal["text"] = "text"
    content: str


class ToxicityItem(BaseModel):
    name: str
    status: Literal["safe", "unsafe", "depends"]
    note: str


class ToxicityReply(BaseModel):
    type: Literal["toxicity"] = "toxicity"
    items: List[ToxicityItem]


class DietReply(BaseModel):
    type: Literal["diet"] = "diet"
    species: str
    weight_kg: float
    life_stage: str
    activity_level: str
    rer_kcal: float
    mer_kcal: float
    explanation: str


Reply = Union[TextReply, ToxicityReply, DietReply]


class ChatResponse(BaseModel):
    reply: Reply = Field(discriminator="type")


# ---- Specialist model classification (breed / skin) -----------------------
# Separate from /api/chat on purpose — these hit the real trained models
# directly (no GPT involved), so the request/response shape is much
# simpler: an image in, a label + confidence out.

class ClassifyRequest(BaseModel):
    image_base64: str


class ClassifyResponse(BaseModel):
    label: str
    confidence: float  # 0-100


# ---- Internal: structured output schema for Food Safety -------------------
# Forces GPT to answer in a shape we can parse deterministically instead of
# free text, so the UI can render a real per-item safety list.

FOOD_SAFETY_JSON_SCHEMA = {
    "name": "food_safety_response",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "on_topic": {
                "type": "boolean",
                "description": (
                    "False if the user's message isn't about checking a "
                    "food/ingredient's safety for a pet (off-topic, belongs "
                    "to another mode, or you need clarification first)."
                ),
            },
            "message": {
                "type": "string",
                "description": (
                    "Used only when on_topic is false: the redirect or "
                    "clarifying question to show the user. Empty string "
                    "when on_topic is true."
                ),
            },
            "items": {
                "type": "array",
                "description": (
                    "One entry per distinct food/ingredient identified. "
                    "Empty when on_topic is false."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["safe", "unsafe", "depends"],
                        },
                        "note": {
                            "type": "string",
                            "description": (
                                "One or two sentences: the mechanism/reason, "
                                "in plain language."
                            ),
                        },
                    },
                    "required": ["name", "status", "note"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["on_topic", "message", "items"],
        "additionalProperties": False,
    },
}


# ---- Internal: tool-calling schema for Diet Expert -------------------------
# GPT drives the conversation (asks for species/weight/life stage/activity),
# but never does the arithmetic itself — once it has everything it needs, it
# calls this tool and the backend computes RER/MER deterministically.

CALCULATE_FEEDING_PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate_feeding_plan",
        "description": (
            "Call this once you have the pet's species, weight in kg, life "
            "stage, and activity level. Do NOT compute RER/MER yourself — "
            "the backend will calculate the exact numbers from these inputs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "species": {
                    "type": "string",
                    "enum": ["dog", "cat"],
                },
                "weight_kg": {
                    "type": "number",
                    "description": "Body weight in kilograms.",
                },
                "life_stage": {
                    "type": "string",
                    "enum": ["puppy_kitten", "adult", "senior"],
                },
                "activity_level": {
                    "type": "string",
                    "enum": ["low", "moderate", "high"],
                    "description": (
                        "Ignored when life_stage is puppy_kitten (growth "
                        "uses its own fixed factor)."
                    ),
                },
            },
            "required": ["species", "weight_kg", "life_stage", "activity_level"],
            "additionalProperties": False,
        },
    },
}
