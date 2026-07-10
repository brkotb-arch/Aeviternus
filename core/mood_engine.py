from core.event_bus import event_bus


MOODS = {
    "NEUTRAL": {
        "valence": 0,
        "arousal": 0,
        "clarity": 0.5
    },

    "SASS_ON": {
        "valence": 0.3,
        "arousal": 0.7,
        "clarity": 0.6
    },

    "DARK": {
        "valence": -0.5,
        "arousal": 0.4,
        "clarity": 0.8
    },

    "SOFT": {
        "valence": 0.5,
        "arousal": -0.3,
        "clarity": 0.7
    },

    "FOCUS": {
        "valence": 0,
        "arousal": 0.8,
        "clarity": 1
    },

    "CHAOS": {
        "valence": -0.2,
        "arousal": 1,
        "clarity": 0.2
    }
}


mood_state = {
    "current": "NEUTRAL",
    "valence": 0,
    "arousal": 0,
    "clarity": 0.5
}


def set_mood(mood):

    if mood not in MOODS:
        return mood_state

    mood_state.update(
        MOODS[mood]
    )

    mood_state["current"] = mood

    event_bus.emit(
        "mood_change",
        mood_state
    )

    return mood_state