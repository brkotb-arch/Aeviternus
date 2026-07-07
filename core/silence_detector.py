# core/silence_detector.py
import time
from core.event_bus import event_bus

class SilenceDetector:
    def __init__(self, threshold=8):
        self.last_activity = time.time()
        self.threshold = threshold
        self.active = True

    def mark_activity(self):
        self.last_activity = time.time()
        self.active = True

    def check_silence(self):
        now = time.time()
        if now - self.last_activity > self.threshold:
            event_bus.emit("silence", {
                "duration": now - self.last_activity
            })
            self.last_activity = now  # reset to avoid spam

silence_detector = SilenceDetector()