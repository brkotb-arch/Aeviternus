import json
import os
import re
import time

from db import add_message
from storage import save_fact


CONFLICT_LOG_PATH = os.path.join("data", "conflict_log.jsonl")


def _write_jsonl(path, payload):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def classify_event(text, role="observation", mood=None):
    text_lower = (text or "").lower()
    if not text_lower.strip():
        return "noise"

    fact_markers = ("запомни", "важно:", "факт:", "remember", "fact:")
    if role == "user" and any(marker in text_lower for marker in fact_markers):
        return "fact"

    if mood and mood not in ("NEUTRAL", "neutral", "нейтральное"):
        return "emotion"

    if len(text_lower) < 3:
        return "noise"

    return "semantic"


def _extract_fact(text):
    cleaned = re.sub(r"^(запомни|факт:|важно:|remember|fact:)\s*", "", text.strip(), flags=re.I)
    key_seed = re.sub(r"\W+", "_", cleaned.lower(), flags=re.U).strip("_")[:40]
    return key_seed or "memory_fact", cleaned


def store_event(text, role="observation", mood=None, semantic_writer=None):
    kind = classify_event(text, role=role, mood=mood)
    if kind == "noise":
        return {"stored": False, "kind": kind}

    if role in ("user", "assistant"):
        add_message(role, text)

    if kind == "fact":
        key, value = _extract_fact(text)
        try:
            save_fact(key, value, "dialogue", 8)
        except Exception as e:
            _write_jsonl(CONFLICT_LOG_PATH, {
                "ts": time.time(),
                "type": "fact_store_error",
                "key": key,
                "error": str(e),
            })

    if kind in ("semantic", "fact") and semantic_writer:
        try:
            semantic_writer(text, role)
        except Exception as e:
            _write_jsonl(CONFLICT_LOG_PATH, {
                "ts": time.time(),
                "type": "semantic_store_error",
                "role": role,
                "error": str(e),
            })

    return {"stored": True, "kind": kind}


def store_dialog_pair(user_text, assistant_text, mood=None, semantic_writer=None):
    user_result = store_event(
        user_text,
        role="user",
        mood=mood,
        semantic_writer=semantic_writer,
    )
    assistant_result = store_event(
        assistant_text,
        role="assistant",
        mood=mood,
        semantic_writer=semantic_writer,
    )
    return {
        "user": user_result,
        "assistant": assistant_result,
    }
