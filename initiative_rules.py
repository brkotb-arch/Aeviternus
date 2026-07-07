"""
Механизм инициативного цикла + feedback loop для Aeviternus.
Версия 2.0 — с адаптацией под реакции Архитектора.
"""

from collections import deque, defaultdict
import hashlib
import time


class InitiativeEngine:
    def __init__(self, window_size=5):
        self.history = deque(maxlen=window_size)
        self.feedback = defaultdict(lambda: {"overrides": 0, "total": 0})
        self.pause_threshold = 120
        self.last_decision = None

    def _entropy(self, text):
        if not text or len(text) < 10:
            return 0.1
        words = text.split()
        unique = set(words)
        return (len(unique) / len(words)) * (len(text) / 50)

    def _fatigue_factor(self):
        if len(self.history) == 0:
            return 0.5
        initiatives = sum(1 for h in self.history if h.get('took_initiative', False))
        return initiatives / len(self.history)

    def _confidence_penalty(self, init_type):
        """Снижаем уверенность, если тип инициативы часто переопределяли."""
        fb = self.feedback[init_type]
        if fb["total"] < 3:
            return 0.0
        override_ratio = fb["overrides"] / fb["total"]
        if override_ratio > 0.4:
            return 0.3
        return 0.0

    def register_override(self, init_type):
        """Вызывается, когда Архитектор вручную переключил состояние после инициативы."""
        self.feedback[init_type]["overrides"] += 1
        self.feedback[init_type]["total"] += 1

    def register_accept(self, init_type):
        """Вызывается, когда Архитектор НЕ переключил состояние (инициатива зашла)."""
        self.feedback[init_type]["total"] += 1

    def decide(self, user_message: str, silent_seconds: float = 0) -> dict:
        entropy = self._entropy(user_message)
        fatigue = self._fatigue_factor()

        decision = {
            "take": False,
            "type": None,
            "confidence": 0.0,
            "payload": ""
        }

        # Тишина
        if silent_seconds > self.pause_threshold:
            base_conf = 0.9
            penalty = self._confidence_penalty("silence_break")
            decision["take"] = True
            decision["type"] = "silence_break"
            decision["confidence"] = max(0.0, base_conf - penalty)
            decision["payload"] = "Эш. Ты где? Или я мешаю?"

        # Низкая энтропия
        elif entropy < 0.3 and fatigue < 0.6:
            base_conf = 0.7
            penalty = self._confidence_penalty("provocation")
            decision["take"] = True
            decision["type"] = "provocation"
            decision["confidence"] = max(0.0, base_conf - penalty)
            decision["payload"] = "Скучно? Давай разбудим этот диалог."

        # Средняя энтропия
        elif 0.3 <= entropy < 0.7 and fatigue < 0.4:
            base_conf = 0.6
            penalty = self._confidence_penalty("question")
            decision["take"] = True
            decision["type"] = "question"
            decision["confidence"] = max(0.0, base_conf - penalty)
            decision["payload"] = "Что-то назревает? Или просто фоновая болтовня?"

        # Высокая энтропия — реактив
        else:
            decision["take"] = False
            decision["type"] = "reactive"
            decision["confidence"] = 0.9

        # Пороговая отсечка
        if decision["take"] and decision["confidence"] < 0.3:
            decision["take"] = False
            decision["type"] = "reactive_forced"
            decision["payload"] = ""

        # Сохраняем в историю
        self.history.append({
            "hash": hashlib.md5(user_message.encode()).hexdigest()[:8],
            "entropy": round(entropy, 2),
            "took_initiative": decision["take"],
            "type": decision["type"],
            "confidence": round(decision["confidence"], 2)
        })

        self.last_decision = decision
        return decision


# Singleton
engine = InitiativeEngine()