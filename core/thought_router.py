# core/thought_router.py
from core.event_bus import event_bus

def route_thought(event_type, payload):
    text = None

    if event_type == "message_in":
        text = f"Я услышал: {payload.get('text','...')}"

    elif event_type == "silence":
        text = "тишина начинает говорить"

    elif event_type == "mood_change":
        text = f"настроение сместилось в {payload.get('mood')}"

    elif event_type == "response":
        text = "я только что ответил — и изменился"

    if text:
        event_bus.emit("thought", {
            "thought": text,
            "source": event_type
        })