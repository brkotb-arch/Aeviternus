class CognitiveContext:

    def __init__(
        self,
        user_message,
        runtime_state=None,
        mood=None,
        identity=None,
        memories=None
    ):

        self.user_message = user_message

        self.runtime_state = runtime_state

        self.mood = mood

        self.identity = identity

        self.memories = memories or []


    def snapshot(self):

        return {
            "message": self.user_message,
            "mood": self.mood,
            "runtime": (
                self.runtime_state.snapshot()
                if self.runtime_state
                else None
            ),
            "identity": self.identity,
            "memories": self.memories
        }