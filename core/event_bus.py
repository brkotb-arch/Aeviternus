# core/event_bus.py
from collections import defaultdict
from queue import Queue
import json
import time

class EventBus:
    def __init__(self):
        self.listeners = defaultdict(list)
        self.stream_clients = []

    def on(self, event_type, callback):
        self.listeners[event_type].append(callback)

    def emit(self, event_type, payload=None):
        event = {
            "type": event_type,
            "payload": payload or {},
            "ts": time.time()
        }

        # обычные listeners
        for cb in self.listeners[event_type]:
            cb(event)

        # stream clients
        for q in self.stream_clients:
            q.put(event)

    # 🔥 SSE STREAM
    def stream(self):
        q = Queue()
        self.stream_clients.append(q)

        try:
            while True:
                event = q.get()
                yield f"data: {json.dumps(event)}\n\n"
        except GeneratorExit:
            self.stream_clients.remove(q)

event_bus = EventBus()