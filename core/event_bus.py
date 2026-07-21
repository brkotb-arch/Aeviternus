# core/event_bus.py
from collections import defaultdict
from queue import Queue
import json
import logging
import threading
import time

logger = logging.getLogger("event_bus")

class EventBus:
    def __init__(self):
        self.listeners = defaultdict(list)
        self.stream_clients = []
        self._clients_lock = threading.Lock()

    def on(self, event_type, callback):
        self.listeners[event_type].append(callback)

    def emit(self, event_type, payload=None):
        event = {
            "type": event_type,
            "payload": payload or {},
            "ts": time.time()
        }

        # обычные listeners — падение одного не должно ронять emit() целиком
        # (emit() вызывается синхронно из /send и других запросов).
        for cb in self.listeners[event_type]:
            try:
                cb(event)
            except Exception:
                logger.exception("EventBus listener failed for %s", event_type)

        # stream clients — список мутируется из stream() при подключении/
        # отключении SSE-клиента, а читается здесь из любого потока, который
        # вызвал emit() (request thread, think_loop, curiosity_loop и т.д.)
        with self._clients_lock:
            clients = list(self.stream_clients)
        for q in clients:
            q.put(event)

    # 🔥 SSE STREAM
    def stream(self):
        q = Queue()
        with self._clients_lock:
            self.stream_clients.append(q)

        try:
            while True:
                event = q.get()
                yield f"data: {json.dumps(event)}\n\n"
        except GeneratorExit:
            with self._clients_lock:
                if q in self.stream_clients:
                    self.stream_clients.remove(q)

event_bus = EventBus()