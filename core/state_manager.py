from datetime import datetime


class RuntimeState:

    def __init__(self):

        self.current_mood = "NEUTRAL"

        self.last_event = None

        self.activity = "idle"

        self.attention = "user"

        self.cognition_mode = "normal"

        self.updated_at = datetime.now()


    def update_mood(self, mood):

        if self.current_mood == mood:
            return

        self.current_mood = mood
        self.updated_at = datetime.now()


    def register_event(self, event):

        self.last_event = event
        self.updated_at = datetime.now()

    def set_activity(self, activity):

        self.activity = activity
        self.updated_at = datetime.now()


    def set_attention(self, attention):

        self.attention = attention
        self.updated_at = datetime.now()


    def set_cognition_mode(self, mode):

        self.cognition_mode = mode
        self.updated_at = datetime.now()

    def snapshot(self):

        return {
            "mood": self.current_mood,
            "activity": self.activity,
            "attention": self.attention,
            "cognition_mode": self.cognition_mode,
            "last_event": self.last_event,
            "updated_at": self.updated_at.isoformat()
        }


runtime_state = RuntimeState()

def process_event(event):

    runtime_state.register_event(event)


    event_type = event.get("type")
    payload = event.get("payload", {})


    if event_type == "mood_switch":

        # Реальный отправитель (app.js, кнопки mood-bar) шлёт {"to": ...}.
        # "state" оставлен как запасной ключ для обратной совместимости,
        # если где-то ещё эмитится mood_switch в старом формате.
        mood = payload.get("to", payload.get("state"))

        if mood:
            runtime_state.update_mood(mood)


    elif event_type == "ui_activity":

        runtime_state.set_activity("active")


    elif event_type == "message_sent":

        runtime_state.set_activity("thinking")


    elif event_type == "response_generated":

        runtime_state.set_activity("speaking")