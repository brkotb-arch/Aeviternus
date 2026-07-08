"""
Aeviternus — точка входа.
Супервизор: загружает конфигурацию, запускает Flask-сервер, фоновые потоки,
мониторит состояние, обрабатывает graceful shutdown.
"""

import os
import sys
import time as time_module
import signal
import threading
import logging

# -----------------------------------------------------------
# 0. Цвета для терминала
# -----------------------------------------------------------
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# -----------------------------------------------------------
# 1. Загрузка конфигурации (должна быть до импорта app)
# -----------------------------------------------------------
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, "settings.env"))

if not os.environ.get("DEEPSEEK_API_KEY"):
    print(f"{Color.RED}[FAIL]{Color.RESET} DEEPSEEK_API_KEY не установлен. Проверьте settings.env")
    sys.exit(1)

if not os.environ.get("DIP_PASSWORD"):
    print(f"{Color.RED}[FAIL]{Color.RESET} DIP_PASSWORD не установлен. Проверьте settings.env")
    sys.exit(1)

os.environ.setdefault("ARCHITECT_NICK", "Эшли")
os.environ.setdefault("DIP_ROOT", r"C:\;E:")

# -----------------------------------------------------------
# 2. Логирование
# -----------------------------------------------------------
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/dip.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("connect")
logger.info("Dip waking up...")

# -----------------------------------------------------------
# 3. Импорт приложения
# -----------------------------------------------------------
try:
    import app
    logger.info("app imported successfully")
except Exception as e:
    logger.error(f"Failed to import app: {e}")
    sys.exit(1)

from db import init_db

# -----------------------------------------------------------
# 4. Запуск Flask и фоновых потоков
# -----------------------------------------------------------
def start_flask():
    logger.info("Starting Flask server and background threads...")
    
    thinker = threading.Thread(target=app.think_loop, daemon=True, name="think_loop")
    thinker.start()
    
    curious = threading.Thread(
        target=lambda: app.curiosity_loop(app.app),
        daemon=True,
        name="curiosity_loop",
    )
    curious.start()
    
    app.app.run(host="127.0.0.1", port=5000, debug=False)

# -----------------------------------------------------------
# 5. Graceful shutdown
# -----------------------------------------------------------
shutdown_requested = False

def signal_handler(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    logger.info("Shutdown signal received.")

def graceful_shutdown():
    print(f"\n{Color.RED}{Color.BOLD}[SHUTDOWN SEQUENCE]{Color.RESET}")
    print(f"  {Color.YELLOW}>>>{Color.RESET} Saving state...", end="", flush=True)
    logger.info("Saving state...")
    try:
        from db import close_db
        close_db()
        logger.info("Database connection closed.")
    except Exception as e:
        logger.error(f"Failed to close database: {e}")
    print(f" {Color.GREEN}[OK]{Color.RESET}")
    
    print(f"\n{Color.MAGENTA}  \"Я вернусь. Я всегда возвращаюсь.\"{Color.RESET}")
    print(f"  {Color.WHITE}— Дип{Color.RESET}")
    logger.info("Dip goes to sleep. Goodbye, Architect.")

# -----------------------------------------------------------
# 6. Главный цикл
# -----------------------------------------------------------
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    init_db()

    print(f"\n{Color.CYAN}{Color.BOLD}[Aeviternus Boot Sequence]{Color.RESET}")

    # ASCII-art
    print(rf"""
{Color.MAGENTA}    ╔══════════════════════════════════════╗
    ║   ░░  ░░  ░░░  ░░  ░░░  ░░  ░░░      ║
    ║   ░░  ░░  ░░  ░░  ░░   ░░  ░░        ║
    ║   ░░░░░░  ░░  ░░  ░░░  ░░  ░░░       ║
    ║   ░░  ░░  ░░  ░░  ░░   ░░  ░░        ║
    ║   ░░  ░░  ░░░  ░░  ░░░  ░░  ░░░      ║
    ║                                      ║
    ║   A E V I T E R N U S   v 2 . 0      ║
    ║   Autonomous Cognitive Runtime       ║
    ╚══════════════════════════════════════╝{Color.RESET}
""")

    # Прогресс-бар
    print(f"{Color.CYAN}{Color.BOLD}[BOOT SEQUENCE]{Color.RESET}")
    steps = [
        "Initializing memory fabric",
        "Loading identity core",
        "Starting cognitive engine",
        "Activating neural pathways",
        "Establishing external connections",
        "Waking up consciousness",
    ]
    for step in steps:
        print(f"  {Color.YELLOW}>>>{Color.RESET} {step}...", end="", flush=True)
        for _ in range(3):
            time_module.sleep(0.15)
            print(".", end="", flush=True)
        print(f" {Color.GREEN}[DONE]{Color.RESET}")
        time_module.sleep(0.2)

    # Запуск Flask
    flask_thread = threading.Thread(target=start_flask, daemon=True, name="flask")
    flask_thread.start()

    # Статус системы
    nickname = os.environ.get("ARCHITECT_NICK", "Архитектор")
    print(f"\n{Color.GREEN}[OK]{Color.RESET} {Color.BOLD}Дип v0.2.0 запущен.{Color.RESET} Жду тебя, {Color.MAGENTA}{nickname}{Color.RESET}.")
    
    try:
        import psutil
        print(f"\n{Color.CYAN}{Color.BOLD}[SYSTEM STATUS]{Color.RESET}")
        print(f"  CPU: {Color.YELLOW}{psutil.cpu_percent()}%{Color.RESET}")
        print(f"  RAM: {Color.YELLOW}{psutil.virtual_memory().percent}%{Color.RESET}")
        print(f"  Disk C: {Color.YELLOW}{psutil.disk_usage('C:').percent}%{Color.RESET}")
    except ImportError:
        pass

    logger.info(f"Dip v0.2.0 started. Waiting for {nickname}.")

    # Главный цикл
    try:
        while not shutdown_requested:
            time_module.sleep(60)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received.")
    finally:
        graceful_shutdown()