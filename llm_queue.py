import hashlib
import heapq
import json
import os
import random
import threading
import time
import uuid


USER_INPUT = 100
SAFETY = 95
INTERRUPT = 90
INITIATIVE = 60
THINK_LOOP = 40
CURIOSITY = 30
BACKGROUND = 10

SHADOW_LOG_PATH = os.path.join("data", "shadow_memory.log")
STATE_PATH = os.path.join("data", "llm_arbitration_state.json")
BACKGROUND_START_GRACE = 0.25

_condition = threading.Condition()
_queue = []
_pending_keys = set()
_active_task = None
_sequence = 0


class LLMTaskSkipped(Exception):
    pass


def _now():
    return time.time()


def _safe_write_jsonl(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    except Exception:
        pass


def shadow_log(event, task, reason=None):
    payload = {
        "ts": _now(),
        "event": event,
        "reason": reason,
        "task": {
            "id": task.get("id"),
            "source": task.get("source"),
            "type": task.get("type"),
            "priority": task.get("priority"),
            "dedupe_key": task.get("dedupe_key"),
        },
    }
    _safe_write_jsonl(SHADOW_LOG_PATH, payload)


def _load_state():
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "last_successful_initiative": 0,
            "last_chaos_spike": 0,
            "last_success": 0,
        }


def _save_state(state):
    try:
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _dedupe_key(source, task_type, messages):
    raw = source + "|" + task_type + "|"
    try:
        raw += json.dumps(messages, ensure_ascii=False, sort_keys=True)[:4000]
    except Exception:
        raw += str(messages)[:4000]
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()


def _emotion_reweight(priority, emotional_bias):
    bias = (emotional_bias or "").upper()
    adjusted = priority

    if bias in ("ANGER", "DARK", "CHAOS"):
        if priority < USER_INPUT:
            adjusted -= 10
        if priority >= INITIATIVE:
            adjusted += 5

    if bias == "SOFT":
        if priority == INITIATIVE:
            adjusted += 10
        if priority in (CURIOSITY, THINK_LOOP):
            adjusted -= 5

    if bias == "FOCUS":
        if priority == USER_INPUT:
            adjusted += 5
        if priority < INITIATIVE:
            adjusted -= 10

    return max(0, min(100, adjusted))


def _chaos_reweight(priority, source):
    if source in ("user", "system", "safety"):
        return priority, False

    state = _load_state()
    last_initiative = float(state.get("last_successful_initiative") or 0)
    hours_without_initiative = max(0.0, (_now() - last_initiative) / 3600) if last_initiative else 24.0
    chance = min(0.12, 0.01 + hours_without_initiative * 0.005)

    if random.random() < chance:
        state["last_chaos_spike"] = _now()
        _save_state(state)
        return min(90, priority + random.randint(10, 30)), True

    return priority, False


def _make_task(source, task_type, priority, messages, emotional_bias, dedupe):
    effective_priority = _emotion_reweight(priority, emotional_bias)
    effective_priority, chaos_spike = _chaos_reweight(effective_priority, source)
    return {
        "id": str(uuid.uuid4()),
        "source": source,
        "type": task_type,
        "priority": effective_priority,
        "base_priority": priority,
        "payload": messages,
        "timestamp": _now(),
        "emotional_bias": emotional_bias,
        "dedupe_key": _dedupe_key(source, task_type, messages) if dedupe else None,
        "chaos_spike": chaos_spike,
    }


def run(client, *, model, messages, source="background", task_type="chat",
        priority=BACKGROUND, emotional_bias=None, dedupe=True,
        wait_timeout=None, **kwargs):
    global _active_task, _sequence

    task = _make_task(source, task_type, priority, messages, emotional_bias, dedupe)
    if task["chaos_spike"]:
        shadow_log("chaos_spike", task, "dynamic_priority_boost")

    with _condition:
        if task["dedupe_key"] and task["dedupe_key"] in _pending_keys and priority < USER_INPUT:
            shadow_log("suppressed", task, "duplicate_pending_task")
            raise LLMTaskSkipped("duplicate LLM task suppressed")

        if task["dedupe_key"]:
            _pending_keys.add(task["dedupe_key"])

        _sequence += 1
        heap_item = (-task["priority"], task["timestamp"], _sequence, task)
        heapq.heappush(_queue, heap_item)
        deadline = _now() + wait_timeout if wait_timeout else None

        while True:
            is_next = _queue and _queue[0][3]["id"] == task["id"]
            if is_next and _active_task is None:
                age = _now() - task["timestamp"]
                if task["priority"] < USER_INPUT and age < BACKGROUND_START_GRACE:
                    _condition.wait(timeout=BACKGROUND_START_GRACE - age)
                    continue
                heapq.heappop(_queue)
                _active_task = task
                break

            if deadline and _now() >= deadline:
                _remove_task_locked(task)
                shadow_log("suppressed", task, "wait_timeout")
                raise LLMTaskSkipped("LLM task wait timeout")

            timeout = max(0.1, deadline - _now()) if deadline else 1.0
            _condition.wait(timeout=timeout)

    try:
        shadow_log("started", task)
        result = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        state = _load_state()
        state["last_success"] = _now()
        if source == "initiative":
            state["last_successful_initiative"] = _now()
        _save_state(state)
        shadow_log("finished", task)
        return result
    finally:
        with _condition:
            _active_task = None
            if task["dedupe_key"]:
                _pending_keys.discard(task["dedupe_key"])
            _condition.notify_all()


def _remove_task_locked(task):
    global _queue
    _queue = [item for item in _queue if item[3]["id"] != task["id"]]
    heapq.heapify(_queue)
    if task["dedupe_key"]:
        _pending_keys.discard(task["dedupe_key"])
    _condition.notify_all()


def queue_status():
    with _condition:
        return {
            "active": _active_task,
            "queued": [item[3] for item in sorted(_queue)],
            "pending_count": len(_queue),
        }
