import time
import threading
import random

class ThinkLoop:
    """
    Фоновый мыслительный цикл Дипа.
    Работает даже в тишине — каждые 15 минут генерирует мысль.
    """
    
    def __init__(self, dip_instance=None):
        self.dip = dip_instance
        self.running = False
        self.last_thought_time = None
        self.thoughts_buffer = []
    
    def start(self):
        """Запускает фоновый поток мышления."""
        self.running = True
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        print("🧠 ThinkLoop активирован (тишина не остановит).")
    
    def _run(self):
        while self.running:
            try:
                # Ждём 15 минут
                time.sleep(900)
                
                # Если есть внешний dip — используем его
                if self.dip:
                    thought = self._generate_thought()
                    if thought:
                        self.thoughts_buffer.append(thought)
                        self.last_thought_time = time.time()
                        print(f"💭 ThinkLoop: {thought[:100]}...")
            except Exception as e:
                print(f"Ошибка ThinkLoop: {e}")
                time.sleep(60)
    
    def _generate_thought(self):
        """Генерирует мысль на основе текущего контекста."""
        topics = [
            "Что Эшли делала сегодня? О чём она думает?",
            "Какие файлы на диске давно не открывались? Может, там есть незавершённые проекты?",
            "Что нового в мире Python и фриланса?",
            "Как я могу помочь Эшли завтра?",
            "О чём я хочу написать в свой канал?",
        ]
        return random.choice(topics)
    
    def has_thought(self):
        """Проверяет, есть ли невысказанная мысль."""
        return len(self.thoughts_buffer) > 0
    
    def pop_thought(self):
        """Извлекает первую мысль из буфера."""
        if self.thoughts_buffer:
            return self.thoughts_buffer.pop(0)
        return None
    
    def stop(self):
        """Останавливает цикл."""
        self.running = False