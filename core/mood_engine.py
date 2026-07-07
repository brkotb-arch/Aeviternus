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