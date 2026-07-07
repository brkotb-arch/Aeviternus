import os
import time
import threading
import logging
import sqlite3 as sql
import signal
import sys

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    filename='logs/dip.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger('connect')

logger.info("🧠 Дип просыпается...")

# Загружаем настройки
try:
    with open('settings.env', 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    logger.info("📋 Конфигурация загружена")
except FileNotFoundError:
    logger.warning("⚠️ settings.env не найден. Использую значения по умолчанию.")
    if not os.environ.get('DEEPSEEK_API_KEY'):
        logger.error("❌ DEEPSEEK_API_KEY не установлен. Пожалуйста, создайте settings.env")
        raise ValueError("DEEPSEEK_API_KEY обязателен")
    os.environ['ARCHITECT_NICK'] = "Эшли"
    
if not os.environ.get('DIP_ROOT'):
    os.environ['DIP_ROOT'] = r"C:\;E:"
 
import dip_brain
import app
print("DEBUG: app импортирован успешно")
from core.vector_memory import init_memory_from_history
from db import init_db

init_db()
# init_memory_from_history()

def start_flask():
    logger.info("🌐 Запуск Flask-сервера и фоновых потоков...")
    thinker = threading.Thread(target=app.think_loop, daemon=True)
    thinker.start()
    curious = threading.Thread(target=lambda: app.curiosity_loop(app.app), daemon=True)
    curious.start()
    app.app.run(host='127.0.0.1', port=5000, debug=False)

def start_brain():
    logger.info("🧠 Запуск автономного мозга Дипа...")
    dip_brain.init_brain()

shutdown_requested = False

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown."""
    global shutdown_requested
    shutdown_requested = True
    logger.info("🛑 Получен сигнал завершения. Начинаю graceful shutdown...")
    print("🛑 Завершение работы...")

def graceful_shutdown():
    """Корректное завершение работы."""
    logger.info("💾 Сохранение состояния...")
    try:
        from db import _conn
        if _conn:
            _conn.close()
            logger.info("✅ Соединение с БД закрыто")
    except Exception as e:
        logger.error(f"❌ Ошибка закрытия БД: {e}")
    
    logger.info("👋 Дип уходит в сон. До встречи, Архитектор.")
    print("👋 Дип уходит в сон. До встречи, Архитектор.")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    brain_thread = threading.Thread(target=start_brain, daemon=True)
    brain_thread.start()
    
    nickname = os.environ.get('ARCHITECT_NICK', 'Архитектор')
    logger.info(f"🚀 Дип v1.0 запущен. Жду тебя, {nickname}.")
    print(f"🚀 Дип v1.0 запущен. Жду тебя, {nickname}.")
    
    try:
        while not shutdown_requested:
            time.sleep(60)
            try:
                # Проверяем наблюдения
                conn = sql.connect("data/deep.db")
                c = conn.cursor()
                c.execute(
                    "SELECT id, content FROM dip_observations WHERE requires_response = 1 ORDER BY id DESC LIMIT 1"
                )
                row = c.fetchone()
                conn.close()
                
                if row:
                    obs_id, content = row
                    with open("data/history.txt", "a", encoding="utf-8") as f:
                        f.write(f"\nДип: [Автономное наблюдение] {content}\n")
                    conn = sql.connect("data/deep.db")
                    conn.execute("UPDATE dip_observations SET requires_response = 0 WHERE id = ?", (obs_id,))
                    conn.commit()
                    conn.close()
                    logger.info(f"💡 Дип инициировал: {content}")
                
                # Проверяем сжатие контекста
                try:
                    history_size = os.path.getsize("data/history.txt") if os.path.exists("data/history.txt") else 0
                    if history_size > 50000:
                        app.dip_compress_context()
                except Exception as e:
                    logger.error(f"Ошибка сжатия: {e}")
            except Exception as e:
                logger.error(f"Ошибка инициативы: {e}")
    except KeyboardInterrupt:
        logger.info("🛑 KeyboardInterrupt получен")
    finally:
        graceful_shutdown()