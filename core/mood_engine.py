# core/mood_engine.py

from core.event_bus import event_bus

mood_state = {
    "valence": 0.0,
    "arousal": 0.0,
    "clarity": 0.5
}

def apply_mood(mood):

    if mood == "positive":
        mood_state["valence"] += 0.1

    if mood == "negative":
        mood_state["valence"] -= 0.1
        mood_state["arousal"] += 0.05

    if mood == "curious":
        mood_state["clarity"] += 0.1

    clamp()

    event_bus.emit("mood_change", mood_state)


def clamp():
    for k in mood_state:
        mood_state[k] = max(-1.0, min(1.0, mood_state[k]))


# --- MoodState (sentiment) entrypoint ---
# app.py импортирует именно set_mood() (см. `from core.mood_engine import
# set_mood` наверху app.py и вызов set_mood(mood) в generate_reply(), где
# mood ∈ {"positive","negative","curious","neutral"}). Это MoodState —
# эмоциональный слой (valence/arousal/clarity), не путать с RuntimeState
# ниже (шесть состояний аватара).
def set_mood(mood):
    apply_mood(mood)
    return dict(mood_state)


# --- RuntimeState (шесть состояний аватара: NEUTRAL/SASS_ON/DARK/SOFT/FOCUS/CHAOS) ---
# Другой словарь понятий, чем MoodState выше: это то, что выбирают кнопки
# mood-bar и что рисует avatar_engine.js. Раньше /mood (POST) и generate_reply()
# оба звали одну и ту же функцию set_mood() с несовместимыми значениями —
# отсюда и коллизия. Теперь у RuntimeState есть отдельное явное имя.
VALID_RUNTIME_STATES = {"NEUTRAL", "SASS_ON", "DARK", "SOFT", "FOCUS", "CHAOS"}
current_runtime_state = "NEUTRAL"


def set_runtime_state(state):
    global current_runtime_state
    if state not in VALID_RUNTIME_STATES:
        state = "NEUTRAL"
    current_runtime_state = state
    event_bus.emit("mood_switch", {"to": current_runtime_state})
    return {"status": "ok", "state": current_runtime_state}