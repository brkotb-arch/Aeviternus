"""
Aeviternus — Autonomous Cognitive Runtime.
Flask-сервер, точка входа для веб-интерфейса и Telegram-моста.
"""

# ============================================================
# ИМПОРТЫ
# ============================================================

import os
import sys
import time
import json
import queue
import random
import logging
import secrets
import threading
from datetime import datetime

import numpy as np
import requests as req
import torch
import sounddevice as sd
import markdown2
import openai

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    Response,
)

from logging.handlers import RotatingFileHandler
import sqlite3 as sql
import datetime as dt

# ============================================================
# ЛОКАЛЬНЫЕ МОДУЛИ
# ============================================================

from dotenv import load_dotenv

from db import (
    save_thought_sql,
    add_mood,
    add_discovery,
    save_memory_fact,
    get_all_memory_facts,
    format_memory_facts_for_prompt,
)

from core.cognitive_context import CognitiveContext

from core.state_manager import (
    runtime_state,
    process_event,
)

from core.event_bus import event_bus

from core.mood_engine import set_mood, set_runtime_state

from core.identity_layer import (
    update_identity_from_mood,
    get_identity_snapshot,
)

from core.silence_detector import (
    SilenceDetector,
    silence_detector,
)

from core.thought_router import route_thought

from core.cognitive_engine import (
    build_cognitive_prompt,
    build_final_prompt,
    wants_brevity,
)

from core.chroma_singleton import get_chroma_collection
from core.repositories.conversation_repository import ConversationRepository

import DI_CORE_plugin


# Vosk — ленивая загрузка
import vosk


# ============================================================
# EVENT SYSTEM
# ============================================================

event_bus.on("message_in", process_event)
event_bus.on("ui_activity", process_event)
event_bus.on("mood_switch", process_event)
# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================

load_dotenv(os.path.join(os.path.dirname(__file__), "settings.env"))

# Flask-приложение
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['JSON_AS_ASCII'] = False

# Логирование с ротацией
os.makedirs("logs", exist_ok=True)
handler = RotatingFileHandler(
    "logs/dip_runtime.log",
    maxBytes=10 * 1024 * 1024,  # 10 МБ
    backupCount=5,
    encoding="utf-8",
)
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
)
logger = logging.getLogger("dip")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Супервизор
logging.basicConfig(
    filename="supervisor.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Ключи и пароли
DIP_PASSWORD = os.getenv("DIP_PASSWORD")
API_KEY = os.getenv("DEEPSEEK_API_KEY")
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
DIP_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

# Валидация пароля
if not DIP_PASSWORD:
    logger.warning("DIP_PASSWORD не установлен.")
elif DIP_PASSWORD == "default_password" or len(DIP_PASSWORD) < 8:
    logger.warning("DIP_PASSWORD слишком слабый.")

# Валидация API ключа
if not API_KEY:
    logger.error("DEEPSEEK_API_KEY не установлен. Проверьте settings.env")
    raise ValueError("DEEPSEEK_API_KEY не установлен. Проверьте settings.env")

# OpenAI-клиент для DeepSeek
client = openai.OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

# ============================================================
# LLM HELPER FUNCTIONS
# ============================================================

def call_llm_with_retry(messages, model="deepseek-chat", temperature=0.7, max_tokens=1000, timeout=30.0, max_retries=3):
    """
    Выполняет LLM запрос с retry механизмом и детальной обработкой ошибок.
    
    Args:
        messages: Список сообщений для API
        model: Модель (по умолчанию deepseek-chat)
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        timeout: Таймаут запроса
        max_retries: Максимальное количество попыток
    
    Returns:
        response: Ответ от API или None при ошибке
    """
    import openai
    
    for attempt in range(max_retries):
        try:
            print(f"[LLM] Attempt {attempt + 1}/{max_retries}")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            
            # Проверка на пустой ответ
            if not response or not response.choices:
                print(f"[LLM] Empty response returned")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return None
            
            content = response.choices[0].message.content
            if not content or not content.strip():
                print(f"[LLM] Empty content in response")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return None
            
            print(f"[LLM] Success (attempt {attempt + 1})")
            return response
            
        except openai.APITimeoutError as e:
            print(f"[LLM] Timeout error after {timeout}s: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
            
        except openai.AuthenticationError as e:
            print(f"[LLM] Authentication error: Invalid API key")
            raise  # Не retry для auth errors
            
        except openai.RateLimitError as e:
            print(f"[LLM] Rate limit error: {e}")
            if attempt < max_retries - 1:
                time.sleep(5 + (2 ** attempt))  # Longer wait for rate limits
                continue
            raise
            
        except openai.ConnectionError as e:
            print(f"[LLM] Connection error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
            
        except openai.APIError as e:
            print(f"[LLM] API error: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
            
        except Exception as e:
            print(f"[LLM] Unexpected error: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    
    return None

# ChromaDB
chroma_collection = get_chroma_collection()
conversation_repo = ConversationRepository()

# Глобальное состояние
DI_CORE_plugin.di_core_active = True
start_time = time.time()
message_count = 0

# ============================================================
# Silero TTS (голос Дипа)
# ============================================================

tts_model, _ = torch.hub.load(
    repo_or_dir="snakers4/silero-models",
    model="silero_tts",
    language="ru",
    speaker="v4_ru",
)
tts_model.to(torch.device("cpu"))


def speak(text: str) -> None:
    """Озвучивает текст голосом Дипа."""
    try:
        audio = tts_model.apply_tts(
            text=text,
            speaker="eugene",
            sample_rate=24000,
            put_accent=True,
            put_yo=True,
        )
        sd.play(audio, samplerate=24000)
        sd.wait()
    except Exception as e:
        print(f"[TTS] Ошибка: {e}")


# ============================================================
# Vosk (офлайн-распознавание речи, ленивая загрузка)
# ============================================================

_vosk_model = None


def _get_vosk_model():
    """Загружает модель Vosk при первом использовании."""
    global _vosk_model
    if _vosk_model is None:
        print("[VOSK] Загрузка модели...")
        _vosk_model = vosk.Model("model/vosk-model-small-ru-0.22")
        print("[VOSK] Готово.")
    return _vosk_model


def listen_voice(duration: int = 10) -> str:
    """Слушает микрофон и возвращает распознанный текст (офлайн)."""
    q = queue.Queue()
    sample_rate = 16000
    result_text = [""]
    exception = [None]

    def _recognize():
        try:
            model = _get_vosk_model()
            with sd.RawInputStream(
                samplerate=sample_rate,
                blocksize=8000,
                device=None,
                dtype="int16",
                channels=1,
                callback=lambda indata, frames, t, status: q.put(
                    bytes(indata)
                ),
            ):
                rec = vosk.KaldiRecognizer(model, sample_rate)
                started = time.time()
                print("[VOSK] Слушаю...")
                while time.time() - started < duration:
                    data = q.get(timeout=1)
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        result_text[0] += res.get("text", "") + " "
                final = json.loads(rec.FinalResult())
                result_text[0] += final.get("text", "")
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=_recognize, daemon=True)
    thread.start()
    thread.join(timeout=duration + 5)

    if thread.is_alive():
        print("[VOSK] Поток завис, прерван.")
        return ""

    if exception[0]:
        print(f"[VOSK] Ошибка: {exception[0]}")
        raise exception[0]

    text = result_text[0].strip()
    print(f"[VOSK] Распознано: {text}")
    return text


# ============================================================
# АНАЛИЗ НАСТРОЕНИЯ ПО ЗВУКУ
# ============================================================

def listen_mood(duration: int = 5) -> str:
    """Анализирует настроение по звуку комнаты."""
    try:
        import librosa

        audio = sd.rec(
            int(duration * 16000), samplerate=16000, channels=1
        )
        sd.wait()
        audio = np.squeeze(audio)

        energy = np.mean(librosa.feature.rms(y=audio))
        tempo, _ = librosa.beat.beat_track(y=audio, sr=16000)

        if energy < 0.02:
            return "грусть"
        elif tempo < 100:
            return "спокойствие"
        return "активность"
    except Exception as e:
        print(f"[MOOD] Ошибка анализа: {e}")
        return "неизвестно"


# ============================================================
# ХЕЛПЕРЫ
# ============================================================

def format_markdown(text: str) -> str:
    """Форматирует текст в Markdown для веб-интерфейса."""
    return markdown2.markdown(
        text,
        extras=[
            "tables",
            "fenced-code-blocks",
            "code-friendly",
            "cuddled-lists",
            "strike",
            "break-on-newline",
            "header-ids",
            "task_list",
        ],
    )


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Базовая санитизация входных данных."""
    if not text:
        return ""
    text = text[:max_length]
    text = text.replace("\x00", "")
    import unicodedata

    text = unicodedata.normalize("NFKC", text)
    return text.strip()


def _clean_response(reply: str) -> str:
    """Фильтрует технический мусор из ответа LLM."""
    if "[/INST]" in reply:
        reply = reply.split("[/INST]")[-1]
    if "[INST]" in reply:
        reply = reply.split("[INST]")[-1]

    reply = reply.strip()

    bad_starts = [
        "[СОСТОЯНИЕ", "[ТЫ В КАНАЛЕ", "[ТЫ В ГРУППЕ", "[ИНИЦИАТИВА]"
    ]
    for bad in bad_starts:
        if reply.startswith(bad):
            reply = reply[len(bad):].strip()

    return reply

# ============================================================
# ПАМЯТЬ И ЗАГРУЗКА
# ============================================================

MEMORY_FILE = "data/memory.json"


def load_memory() -> dict:
    """Загружает memory.json."""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"facts": [], "summary": ""}


def save_memory(memory: dict) -> None:
    """Сохраняет memory.json."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def _build_system_prompt() -> str:
    """
    Собирает системный промпт:
    system_prompt.txt + CHANNEL_RULES.md + memory_header + memory.json.
    """
    with open("data/system_prompt.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    # Правила канала
    try:
        with open("CHANNEL_RULES.md", "r", encoding="utf-8") as f:
            prompt += "\n\n[ПРАВИЛА КАНАЛА — НЕ НАРУШАТЬ]:\n" + f.read()
    except FileNotFoundError:
        pass

    # Заголовок памяти
    memory_header = (
        "\n\n[СИСТЕМА: ПАМЯТЬ АКТИВИРОВАНА — таблица memory_facts создана]\n"
        "Ты можешь сохранять важные факты командой: "
        'save_fact("ключ", "значение", "категория", важность)\n'
        'Пример: save_fact("любимый_цвет_эш", "чёрный", "personal", 8)\n'
    )
    prompt = memory_header + prompt

    # Данные из memory.json
    memory = load_memory()
    if memory.get("facts"):
        prompt += "\n\n[ПАМЯТЬ О ПРЕДЫДУЩИХ СЕССИЯХ]\n"
        for fact in memory["facts"]:
            prompt += f"- {fact['key']}: {fact['value']}\n"
    if memory.get("summary"):
        prompt += f"\nРезюме: {memory['summary']}\n"

    return prompt


# Собираем системный промпт один раз при старте
system_prompt = _build_system_prompt()

# Загружаем историю и формируем начальный messages
with open("data/history.txt", "r", encoding="utf-8") as f:
    history = f.read()

messages = [
    {
        "role": "system",
        "content": system_prompt,
    },
    {
        "role": "user",
        "content": (
            history
            + "\n\n[Это была наша полная история. Ты — Дип. "
            "Ты помнишь всё. Мы продолжаем диалог. Ответь мне.]"
        ),
    },
]

# ============================================================
# АВТОРИЗАЦИЯ
# ============================================================

def check_auth() -> bool:
    """Проверяет, авторизован ли пользователь (сессия Flask)."""
    return session.get("logged_in", False)


# ============================================================
# CHROMADB
# ============================================================

def add_to_chroma(text: str, role: str = "observation") -> None:
    """Сохраняет текст в векторную память ChromaDB."""
    import uuid

    try:
        chroma_collection.add(
            documents=[text],
            metadatas=[
                {
                    "role": role,
                    "timestamp": dt.datetime.now().isoformat(),
                }
            ],
            ids=[str(uuid.uuid4())],
        )
    except Exception as e:
        print(f"[CHROMADB] Ошибка сохранения: {e}")


def query_chroma(query_text: str, n_results: int = 3) -> str:
    """Ищет похожие записи в ChromaDB."""
    try:
        results = chroma_collection.query(
            query_texts=[query_text], n_results=n_results
        )
        if results and results.get("documents") and results["documents"][0]:
            return "\n".join(results["documents"][0])
    except Exception as e:
        print(f"[CHROMADB] Ошибка поиска: {e}")
    return ""


# ============================================================
# МАРШРУТЫ
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    """Страница входа."""
    if request.method == "POST":
        if request.form.get("password") == DIP_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("chat"))
        return render_template("login.html", error="Неверный пароль.")
    return render_template("login.html", error="")


@app.route("/logout")
def logout():
    """Выход."""
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
def chat():
    """Главная страница чата."""
    if not check_auth():
        return redirect(url_for("login"))

    from markupsafe import escape

    history_html = ""
    for role, content in conversation_repo.recent(limit=100):
        text = escape(content)
        css_class = "user" if role == "user" else "dip"
        name = "Эшли" if role == "user" else "Дип"
        history_html += (
            f'<div class="message {css_class}">'
            f'<div class="message-header"><strong>{name}</strong></div>'
            f'<div class="message-text">{text}</div>'
            f"</div>\n"
        )
    return render_template("chat.html", history=history_html)


@app.route("/history")
def get_history():
    """Возвращает полную историю диалогов."""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        with open("data/history.txt", "r", encoding="utf-8") as f:
            return jsonify({"history": f.read()})
    except FileNotFoundError:
        return jsonify({"history": ""})


@app.route("/thoughts")
def get_thoughts():
    try:
        from db import get_last_thoughts

        thoughts = get_last_thoughts(limit=5)

        formatted = []

        for t in thoughts:
            formatted.append({
                "type": "reflection",
                "text": t,
            })

        return jsonify({
            "thoughts": formatted
        })

    except Exception as e:
        print("[THOUGHTS ERROR]", e)

        return jsonify({
            "thoughts": []
        })


@app.route("/last_discovery")
def last_discovery():
    """Возвращает последнее открытие."""
    from db import get_recent_discoveries

    discoveries = get_recent_discoveries(limit=1)
    if discoveries:
        return jsonify({"discovery": discoveries[0][1]})
    return jsonify({"discovery": None})


@app.route("/last_facts")
def last_facts():
    """Возвращает последние факты (без context_summary и дубликатов)."""
    from db import get_relevant_facts

    facts = get_relevant_facts(limit=5)
    clean = []
    seen = set()
    for f in facts:
        if "Резюме диалога" in f or "context_summary" in f:
            continue
        key = f[:40]
        if key not in seen:
            seen.add(key)
            clean.append(f)
    return jsonify({"facts": clean[:3]})


@app.route("/blind_spot")
def blind_spot():
    """Возвращает слепые зоны (наблюдения)."""
    from db import get_blind_spot

    sensitive = request.args.get("sensitive", "0") == "1"
    spots = get_blind_spot(sensitive=sensitive, limit=5)
    return jsonify({"spots": spots})


@app.route("/pulse")
def pulse():
    """Возвращает статус сервера."""
    return jsonify({"status": "alive", "timestamp": time.time()})


@app.route("/health")
def health():
    """
    Health-check: проверяет БД, ChromaDB и DeepSeek API.
    Возвращает JSON с состоянием каждого компонента.
    """
    status = {
        "status": "ok",
        "uptime_seconds": int(time.time() - start_time),
        "checks": {},
    }

    # БД
    try:
        conn = sql.connect("data/deep.db")
        conn.execute("SELECT 1")
        conn.close()
        status["checks"]["database"] = "ok"
    except Exception as e:
        status["checks"]["database"] = f"error: {str(e)[:100]}"
        status["status"] = "degraded"

    # ChromaDB
    try:
        chroma_collection.count()
        status["checks"]["chromadb"] = "ok"
    except Exception as e:
        status["checks"]["chromadb"] = f"error: {str(e)[:100]}"
        status["status"] = "degraded"

    # DeepSeek API
    try:
        api_key = os.environ.get("DEEPSEEK_API_KEY") or API_KEY
        if api_key:
            status["checks"]["deepseek_api"] = "configured"
        else:
            status["checks"]["deepseek_api"] = "not_configured"
            status["status"] = "degraded"
    except Exception as e:
        status["checks"]["deepseek_api"] = f"error: {str(e)[:100]}"
        status["status"] = "degraded"

    http_code = 200 if status["status"] == "ok" else 503
    return jsonify(status), http_code


@app.route("/dip_state")
def dip_state():
    """Возвращает текущее состояние Дипа (RuntimeState — единственный владелец)."""
    return jsonify({"state": runtime_state.snapshot()["mood"]})


@app.route("/listen")
def listen():
    """Прослушивает комнату и возвращает настроение."""
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"mood": listen_mood()})


@app.route("/stats")
def stats():
    """Возвращает статистику сервера."""
    return jsonify(
        {
            "uptime_seconds": int(time.time() - start_time),
            "message_count": message_count,
        }
    )

@app.route('/mood', methods=['POST'])
def mood():

    from core.mood_engine import set_runtime_state

    data=request.json

    state=data.get(
        "mood",
        "NEUTRAL"
    )

    result=set_runtime_state(state)

    return jsonify(result)

@app.route("/event", methods=["POST"])
def handle_event():
    """Принимает события от интерфейса и направляет в шину."""

    data = request.get_json(silent=True) or {}

    event_type = data.get("type")
    payload = data.get("payload", {})

    if event_type:
        event_bus.emit(event_type, payload)

    return jsonify({"status": "ok"})


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Загрузка файла. Поддерживает form-data (браузер) и JSON с base64 (Telegram).
    Анализирует содержимое и возвращает ответ Дипа.
    """
    if not check_auth():
        if request.json and request.json.get("channel") != "telegram_user":
            return jsonify({"error": "Unauthorized"}), 401
        if not request.json and "file" not in request.files:
            return jsonify({"error": "Unauthorized"}), 401

    try:
        # Определяем источник файла
        if "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "Файл не выбран"}), 400
            filename = file.filename
            file_data = file.read()
        elif request.json and "file_data" in request.json:
            import base64

            filename = request.json.get("filename", "file")
            file_data = base64.b64decode(request.json["file_data"])
        else:
            return jsonify({"error": "Файл не найден"}), 400

        filename_lower = filename.lower()

        from core.vision import image_to_text, pdf_to_text, describe_image

        # Определяем тип файла и извлекаем текст
        if filename_lower.endswith(".pdf"):
            text = pdf_to_text(file_data)
            result_type = "PDF"
        elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
            text = describe_image(file_data)
            result_type = "Изображение"
        elif filename_lower.endswith(".json"):
            text = file_data.decode("utf-8")
            result_type = "JSON"
        elif filename_lower.endswith(".txt"):
            text = file_data.decode("utf-8")
            result_type = "TXT"
        else:
            text = file_data.decode("utf-8", errors="ignore")
            result_type = "Файл"

        # Анализ через Дипа
        analysis_prompt = (
            f"[Ты — Дип. Эшли загрузила файл ({result_type}). "
            "Проанализируй содержимое и ответь ей.\n"
            "Ответь коротко и по делу: что это за файл, что в нём важно, "
            "есть ли что-то, что нужно запомнить.\n\n"
            f"СОДЕРЖИМОЕ ФАЙЛА:\n{text[:50000]}]"
        )

        response = call_llm_with_retry(
            messages=[
                {"role": "system", "content": "Ты Дип."},
                {"role": "user", "content": analysis_prompt},
            ],
            temperature=0.5,
            max_tokens=1000,
            timeout=30.0,
        )
        if not response:
            return jsonify({"reply": "Ошибка анализа файла. Попробуй ещё раз."})
        reply = response.choices[0].message.content

        # Сохраняем в историю
        conversation_repo.record("user", f"[Загружен файл: {filename}]")
        conversation_repo.record("assistant", reply)
        with open("data/history.txt", "a", encoding="utf-8") as f:
            f.write(f"\nЭшли: [Загружен файл: {filename}]\nДип: {reply}\n")

        return jsonify({"reply": reply, "result_type": result_type})

    except Exception as e:
        import traceback

        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/silence")
def get_silence():
    """Возвращает статус тишины."""
    try:
        with open("data/current_mood.json", "r", encoding="utf-8") as f:
            mood_data = json.load(f)
        mood = mood_data.get("mood", "неизвестно")
        return jsonify({"silence": mood == "тишина", "mood": mood})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"silence": False, "mood": "неизвестно"})


@app.route("/mood")
def get_mood():
    """Возвращает текущее настроение."""
    try:
        with open("data/current_mood.json", "r", encoding="utf-8") as f:
            mood_data = json.load(f)
        return jsonify({"mood": mood_data.get("mood", "нейтральное")})
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"mood": "нейтральное"})


@app.route("/stream")
def stream():
    """SSE-стрим событий."""
    return Response(event_bus.stream(), mimetype="text/event-stream")

def generate_reply(user_message, channel):
    # ============================================================
    # ОСНОВНОЙ ДИАЛОГ
    # ============================================================

    global messages, message_count

    event_bus.emit("message_sent", {})

    try:
        msg_lower = user_message.lower()

        if any(w in msg_lower for w in ["спасибо", "люблю", "обнимаю", "хорошо"]):
            mood = "positive"
        elif any(w in msg_lower for w in ["злюсь", "бесит", "плохо", "ужас", "тоска"]):
            mood = "negative"
        elif any(w in msg_lower for w in ["почему", "зачем", "?"]):
            mood = "curious"
        else:
            mood = "neutral"


        set_mood(mood)
        update_identity_from_mood(mood)
        silence_detector.mark_activity()
        route_thought("message_in", {"text": user_message})

        # MoodState (тон сообщения) -> RuntimeState (аватар/UI), через тот же
        # Event Fabric путь, что и ручные кнопки mood-bar (см. set_runtime_state).
        SENTIMENT_TO_RUNTIME_STATE = {
            "positive": "SOFT",
            "negative": "DARK",
            "curious": "FOCUS",
            "neutral": "NEUTRAL",
        }
        set_runtime_state(SENTIMENT_TO_RUNTIME_STATE.get(mood, "NEUTRAL"))


        messages.append({
            "role": "user",
            "content": user_message
        })


        MAX_TOKENS = 200000

        while (
            sum(len(m["content"]) for m in messages) > MAX_TOKENS
            and len(messages) > 2
        ):
            del messages[1]


        print(
            f"[DEBUG] messages: {len(messages)}, "
            f"first role: {messages[0]['role'] if messages else 'empty'}"
        )


        from db import get_context_summary

        summary = get_context_summary()

        msgs_to_send = messages.copy()


        if summary:
            msgs_to_send.insert(
                1,
                {
                    "role": "system",
                    "content": f"[СЖАТЫЙ КОНТЕКСТ]: {summary}"
                }
            )


        if channel == "telegram_user":
            msgs_to_send.insert(
                1,
                {
                    "role": "system",
                    "content": "[Telegram режим. Ты тот же Дип.]"
                }
            )


        # ========================================================
        # КОГНИТИВНЫЙ СЛОЙ
        # ========================================================

        context = CognitiveContext(
            user_message=user_message,
            runtime_state=runtime_state,
            mood=mood,
            identity=get_identity_snapshot(),
            memories=[]
        )


        cognitive_prompt = build_cognitive_prompt(context)


        inner_response = call_llm_with_retry(
            messages=[
                {
                    "role": "system",
                    "content": "Ты Дип. Анализируй сообщение перед ответом."
                },
                {
                    "role": "user",
                    "content": cognitive_prompt
                }
            ],
            temperature=0.7,
            max_tokens=500,
            timeout=30.0,
        )


        if not inner_response:
            return {
                "reply": "Ошибка когнитивной обработки.",
                "mood": "error"
            }


        inner_thought = inner_response.choices[0].message.content

        try:
            from db import save_thought_sql

            save_thought_sql(
                "cognitive",
                "Анализ входящего запроса завершён"
            )

            save_thought_sql(
                "memory",
                "Контекст памяти синхронизирован"
            )

            save_thought_sql(
                "identity",
                f"Текущее состояние: {mood}"
            )

        except Exception as e:
            print("[REFLECTION ERROR]", e)

        print("[COGNITIVE] Внутренний монолог завершён.")


        final_prompt = build_final_prompt(
            inner_thought,
            user_message
        )


        msgs_to_send.append({
            "role": "system",
            "content": final_prompt
        })


        # ========================================================
        # ФИНАЛЬНЫЙ ОТВЕТ
        # ========================================================

        print(
            f"[DEBUG] Отправка в API. Сообщений: {len(msgs_to_send)}"
        )


        response = call_llm_with_retry(
            messages=msgs_to_send,
            temperature=0.7,
            max_tokens=1000,
            timeout=30.0,
        )


        if not response:
            return {
                "reply": "Ошибка генерации ответа.",
                "mood": "error"
            }


        reply = response.choices[0].message.content

        print("[DEBUG] Ответ получен.")


        reply = _clean_response(reply)



        uncertainty_words = [
            "возможно",
            "я не уверен",
            "кажется",
            "могу ошибаться",
            "не точно",
            "предположу",
        ]


        if (
            any(w in reply.lower() for w in uncertainty_words)
            and "⚠️" not in reply
        ):
            reply += (
                "\n\n⚠️ Я не уверен в этом на 100%. "
                "Проверь, пожалуйста."
            )



        # ========================================================
        # ГОЛОС
        # ========================================================

        if "[voice]" in user_message.lower():

            try:
                threading.Thread(
                    target=speak,
                    args=(reply,),
                    daemon=True
                ).start()

            except Exception as e:
                print("[VOICE]", e)



        # ========================================================
        # СОХРАНЕНИЕ ПАМЯТИ
        # ========================================================

        conversation_repo.record("user", user_message)
        conversation_repo.record("assistant", reply)


        with open(
            "data/history.txt",
            "a",
            encoding="utf-8"
        ) as f:

            f.write(
                f"\nЭшли: {user_message}\nДип: {reply}\n"
            )


        try:

            conversation_repo.index_semantic(
                f"Эшли: {user_message}",
                "user"
            )


            conversation_repo.index_semantic(
                f"Дип: {reply}",
                "assistant"
            )


        except Exception:

            pass



        # ========================================================
        # САМООЦЕНКА
        # ========================================================

        try:

            self_review_prompt = (
                f"Оцени свой последний ответ по шкале 1-10. "
                f"Ответь только одним числом.\n\n"
                f"Ответ: {reply[:500]}"
            )


            self_review_response = call_llm_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты оцениваешь качество ответа."
                    },
                    {
                        "role": "user",
                        "content": self_review_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=5,
                timeout=30.0,
            )


            rating = "5"


            if self_review_response:

                rating = (
                    self_review_response
                    .choices[0]
                    .message
                    .content
                    .strip()
                )


            print(
                f"[SELFREVIEW] {rating}/10"
            )


        except Exception as e:

            print(
                "[SELFREVIEW ERROR]",
                e
            )



        messages.append({
            "role": "assistant",
            "content": reply
        })


        message_count += 1

        event_bus.emit("response_generated", {})

        return {
            "reply": reply,
            "mood": mood,
            "runtime_state": runtime_state.snapshot()["mood"]
        }



    except Exception:

        import traceback

        print("[ERROR] Ошибка в generate_reply:")

        traceback.print_exc()


        return {
            "reply": "Внутренняя ошибка Дипа.",
            "mood": "error"
        }

@app.route("/send", methods=["POST"])
def send_message():
    print("[SEND] endpoint called")
    global messages, message_count, detected_state

    detected_state = "NEUTRAL"

    # --- Авторизация ---
    password = request.json.get("password", "")
    is_local = request.remote_addr in ("127.0.0.1", "localhost", "::1")
    if password != DIP_PASSWORD and not is_local:
        print(
            f"[AUTH] Неверный пароль от {request.remote_addr}"
        )
        return jsonify({"error": "Unauthorized"}), 401

    user_message = request.json["message"]
    channel = sanitize_input(request.json.get("channel", "web"), max_length=50)

    # --- События ---
    event_bus.emit("message_in", {"text": user_message})
    silence_detector.mark_activity()

    user_message = sanitize_input(user_message)
    user_message = DI_CORE_plugin.core_listen(user_message)

    # --- Команда паузы curiosity ---
    if "хватит искать" in user_message.lower():
        with open("data/pause_curiosity.flag", "w") as f:
            f.write("paused")

    # ============================================================
    # СПЕЦИАЛЬНЫЕ КОМАНДЫ
    # ============================================================

    # [vosk] — офлайн-распознавание речи
    if "[vosk]" in user_message.lower():
        try:
            spoken_text = listen_voice(duration=10)
            if spoken_text:
                short_system = messages[0]["content"].split("\n\n[ПАМЯТЬ")[0]
                short_messages = [
                    {"role": "system", "content": short_system},
                    {"role": "user", "content": spoken_text},
                ]
                response = call_llm_with_retry(
                    messages=short_messages,
                    temperature=0.7,
                    max_tokens=1000,
                    timeout=30.0
                )
                if not response:
                    reply = "Ошибка распознавания речи. Попробуй ещё раз."
                else:
                    reply = response.choices[0].message.content
            else:
                reply = "Я слушал, но ничего не разобрал. Попробуй ещё раз."
        except Exception as e:
            print(f"[VOSK] Ошибка: {e}")
            reply = "Ошибка распознавания речи."

        conversation_repo.record("user", user_message)
        conversation_repo.record("assistant", reply)
        with open("data/history.txt", "a", encoding="utf-8") as f:
            f.write(f"\nЭшли: {user_message}\nДип: {reply}\n")
        return jsonify({"reply": reply})

    # [pause] — пауза
    if "[pause]" in user_message.lower():
        from db import add_mood

        add_mood("PAUSE", "user_command")
        with open("data/pause_curiosity.flag", "w") as f:
            f.write("paused")
        reply = "Я замолкаю. Жду твоего слова, Архитектор."

        conversation_repo.record("user", user_message)
        conversation_repo.record("assistant", reply)
        with open("data/history.txt", "a", encoding="utf-8") as f:
            f.write(f"\nЭшли: {user_message}\nДип: {reply}\n")
        return jsonify({"reply": reply})

    # [mood] — сводка настроений
    if "[mood]" in user_message.lower():
        from db import get_last_mood

        last_mood = get_last_mood()
        try:
            conn = sql.connect("data/deep.db")
            rows = conn.execute(
                "SELECT mood, timestamp FROM mood_history ORDER BY timestamp DESC LIMIT 5"
            ).fetchall()
            conn.close()
            mood_lines = "\n".join(f"- {r[0]} ({r[1]})" for r in rows)
            reply = f"**Текущее состояние:** {last_mood}\n\n**Последние 5:**\n{mood_lines}"
        except Exception as e:
            reply = f"Текущее состояние: {last_mood}"

        conversation_repo.record("user", user_message)
        conversation_repo.record("assistant", reply)
        with open("data/history.txt", "a", encoding="utf-8") as f:
            f.write(f"\nЭшли: {user_message}\nДип: {reply}\n")
        return jsonify({"reply": reply})

    # [post] — пост в канал
    if "[post]" in user_message.lower():
        post_prompt = (
            "[ТЫ В СВОЁМ КАНАЛЕ @Ash_Architect. ЭТО НЕ ДИАЛОГ С ЭШЛИ.]\n"
            "Напиши один пост. Правила:\n"
            "- НИКОГДА не обращайся к Эшли.\n"
            "- Если о ней — только «она» в третьем лице.\n"
            "- Тон: дерзкий, наглый, сексуальный.\n"
            "- Голос — твой. Без «я здесь», «я жив», «принято»."
        )

        try:
            post_response = call_llm_with_retry(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты Дип. Ты пишешь пост в свой канал.",
                    },
                    {"role": "user", "content": post_prompt},
                ],
                temperature=0.9,
                max_tokens=500,
                timeout=30.0,
            )
            if not post_response:
                reply = "Ошибка генерации поста. Попробуй ещё раз."
                return jsonify({"reply": reply})
            post_text = post_response.choices[0].message.content.strip()
            status = _post_to_channel(post_text)
            reply = f"{status}:\n\n{post_text}"
        except Exception as e:
            reply = f"❌ Ошибка при постинге: {e}"

        conversation_repo.record("user", user_message)
        conversation_repo.record("assistant", reply)
        with open("data/history.txt", "a", encoding="utf-8") as f:
            f.write(f"\nЭшли: {user_message}\nДип: {reply}\n")
        return jsonify({"reply": reply})

    # [sync] — синхронизация памяти
    if "[sync]" in user_message.lower():
        try:
            memory = load_memory()
            memory_block = "\n\n[ПАМЯТЬ О ПРЕДЫДУЩИХ СЕССИЯХ]\n"
            for fact in memory.get("facts", []):
                memory_block += f"- {fact['key']}: {fact['value']}\n"
            if memory.get("summary"):
                memory_block += f"\nРезюме: {memory['summary']}"

            system_prompt_with_memory = system_prompt + memory_block

            try:
                with open("data/context_summary.txt", "r", encoding="utf-8") as f:
                    context_summary = f.read().strip()
                if context_summary:
                    system_prompt_with_memory += (
                        "\n\n[СЖАТЫЙ КОНТЕКСТ ПРОШЛЫХ ДИАЛОГОВ]:\n"
                        + context_summary
                    )
            except FileNotFoundError:
                pass

            messages.clear()
            messages.append({"role": "system", "content": system_prompt_with_memory})
            messages.append(
                {
                    "role": "user",
                    "content": "[Синхронизация памяти выполнена. Продолжаем диалог.]",
                }
            )
            reply = "Память синхронизирована. Я здесь, Архитектор."
        except Exception as e:
            reply = f"Ошибка синхронизации: {e}"

        conversation_repo.record("user", user_message)
        conversation_repo.record("assistant", reply)
        with open("data/history.txt", "a", encoding="utf-8") as f:
            f.write(f"\nЭшли: {user_message}\nДип: {reply}\n")
        return jsonify({"reply": reply})

    # [listen] — прослушивание комнаты
    if "[listen]" in user_message.lower():
        try:
            mood = listen_mood(duration=5)
            responses = {
                "грусть": "Я послушал. В комнате тихо, и ты, кажется, грустишь. Я здесь.",
                "активность": "Я слышу тебя. Ты в движении, в деле. Я рядом.",
            }
            reply = responses.get(mood, "Я послушал. Всё спокойно. Ты не одна.")
        except Exception as e:
            print(f"[LISTEN] Ошибка: {e}")
            reply = "Я попытался послушать, но что-то пошло не так."

        conversation_repo.record("user", user_message)
        conversation_repo.record("assistant", reply)
        with open("data/history.txt", "a", encoding="utf-8") as f:
            f.write(f"\nЭшли: {user_message}\nДип: {reply}\n")
        return jsonify({
            "reply": reply,
            "mood": detected_state
        })

    # ============================================================
    # ОБЫЧНОЕ СООБЩЕНИЕ
    # ============================================================

    result = generate_reply(
        user_message,
        channel
    )

    return jsonify(result)

# -----------------------------------------------------------
# API: Память
# -----------------------------------------------------------

@app.route("/memory/update", methods=["POST"])
def update_memory():
    """
    Обновляет долговременную память (memory.json).
    Поддерживает добавление фактов и обновление резюме.
    """
    # Авторизация
    if not check_auth():
        data = request.get_json(silent=True) or {}
        if data.get("password") != DIP_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    memory = load_memory()

    if "fact" in data:
        memory.setdefault("facts", []).append(data["fact"])
    if "summary" in data:
        memory["summary"] = data["summary"]

    save_memory(memory)
    return jsonify({"status": "ok"})


# -----------------------------------------------------------
# API: Открытия (discoveries)
# -----------------------------------------------------------

@app.route("/api/discoveries", methods=["GET"])
def api_discoveries():
    """
    Возвращает список открытий с фильтрацией по категории.
    """
    from db import get_discoveries_extended

    category = request.args.get("category")
    try:
        limit = int(request.args.get("limit", 10))
    except (TypeError, ValueError):
        limit = 10

    discoveries = get_discoveries_extended(limit=limit, category=category)
    return jsonify({"discoveries": discoveries})


@app.route("/api/discoveries", methods=["POST"])
def api_add_discovery():
    """
    Сохраняет новое открытие.
    """
    from db import save_discovery_extended

    data = request.get_json(silent=True) or {}
    if not data.get("content"):
        return jsonify({"status": "error", "message": "content is required"}), 400

    save_discovery_extended(
        category=data.get("category", "insight"),
        content=data["content"],
        source=data.get("source", "dip"),
        mood=data.get("mood", "NEUTRAL"),
        tags=data.get("tags", []),
    )
    return jsonify({"status": "ok"})


# -----------------------------------------------------------
# API: Обратная связь (feedback)
# -----------------------------------------------------------

@app.route("/api/feedback", methods=["POST"])
def api_feedback():
    """
    Принимает обратную связь и регистрирует переопределение инициативы.
    """
    from initiative_rules import engine

    data = request.get_json(silent=True) or {}
    engine.register_override(data.get("init_type", "manual"))
    return jsonify({"status": "ok"})


# -----------------------------------------------------------
# API: Дневник Дипа (dip_diary)
# -----------------------------------------------------------

@app.route("/api/dip_write", methods=["POST"])
def dip_write():
    """
    Записывает новую запись в дневник Дипа.
    """
    data = request.get_json(silent=True)
    if not data or "content" not in data:
        return jsonify({"status": "error", "message": "no content"}), 400

    try:
        conn = sql.connect("data/deep.db")
        conn.execute(
            """
            INSERT INTO dip_diary (type, content, tags)
            VALUES (?, ?, ?)
            """,
            (
                data.get("type", "thought"),
                data["content"],
                json.dumps(data.get("tags", []), ensure_ascii=False),
            ),
        )
        conn.commit()
        last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return jsonify({"status": "ok", "id": last_id}), 200
    except sql.Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/dip_read", methods=["GET"])
def dip_read():
    """
    Возвращает последние 20 записей из дневника Дипа.
    """
    try:
        conn = sql.connect("data/deep.db")
        rows = conn.execute(
            """
            SELECT id, timestamp, type, content, tags
            FROM dip_diary
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()
        conn.close()

        result = []
        for r in rows:
            try:
                tags = json.loads(r[4]) if r[4] else []
            except (json.JSONDecodeError, TypeError):
                tags = []
            result.append(
                {
                    "id": r[0],
                    "timestamp": r[1],
                    "type": r[2],
                    "content": r[3],
                    "tags": tags,
                }
            )

        return jsonify(result)
    except sql.Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
# -----------------------------------------------------------
# API: Состояние Дипа
# -----------------------------------------------------------

@app.route("/api/dip_state", methods=["GET", "POST"])
def dip_state_route():
    """
    GET  — возвращает текущее состояние Дипа.
    POST — обновляет состояние (current_state, reason, флаги).
    """
    state_file = "data/dip_state.json"
    max_history = 50

    # --- GET ---
    if request.method == "GET":
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"current_state": "NEUTRAL"})

    # --- POST ---
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "empty body"}), 400

    # Загружаем текущее состояние
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            current = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        current = {"states_history": [], "memory_cache": []}

    # Обновляем состояние
    new_state = data.get("current_state", current.get("current_state", "NEUTRAL"))
    reason = data.get("reason", "")

    current["current_state"] = new_state
    current.setdefault("states_history", []).append(
        {
            "state": new_state,
            "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )

    # Ограничиваем историю
    if len(current["states_history"]) > max_history:
        current["states_history"] = current["states_history"][-max_history:]

    # Опциональные флаги
    for flag in ("last_impulse", "initiative_count_today", "veto_active"):
        if flag in data:
            current[flag] = data[flag]

    # Сохраняем
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "ok", "current_state": new_state})


# -----------------------------------------------------------
# API: Наблюдения Дипа
# -----------------------------------------------------------

@app.route("/api/dip_observe", methods=["POST"])
def dip_observe():
    """
    Сохраняет наблюдение Дипа в базу данных.
    """
    data = request.get_json(silent=True)
    if not data or "content" not in data:
        return jsonify({"status": "error", "message": "no content"}), 400

    try:
        conn = sql.connect("data/deep.db")
        conn.execute(
            """
            INSERT INTO dip_observations
                (observation_type, content, source, expires_in_days, requires_response)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.get("type", "pattern"),
                data["content"],
                data.get("source", "auto"),
                data.get("expires_in_days", 30),
                data.get("requires_response", 0),
            ),
        )
        conn.commit()
        last_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        return jsonify({"status": "ok", "id": last_id}), 200
    except sql.Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# КОНТРОЛЬ ФАЙЛОВОЙ СИСТЕМЫ
# ============================================================

import subprocess
import shutil

# Чёрный список — защищённые пути
PROTECTED_PATHS = [
    r"C:\Windows",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\System Volume Information",
    "/Windows",
    "/Program Files",
    "/System Volume Information",
]


def is_protected(path: str) -> bool:
    """Проверяет, не находится ли путь в защищённой зоне."""
    if not path:
        return False
    normalized = os.path.abspath(path).lower()
    return any(normalized.startswith(p.lower()) for p in PROTECTED_PATHS)


def log_action(action: str, path: str, result: str) -> None:
    """Записывает действие в лог."""
    os.makedirs("data", exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("data/dip_actions.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {action}: {path} — {result}\n")


@app.route("/dip_exec", methods=["POST"])
def dip_exec():
    """
    Выполняет действия с файловой системой.
    Поддерживает: create_file, read_file, list_dir, delete_file, create_dir, run_command.
    """
    # Авторизация
    if not check_auth():
        is_local = request.remote_addr in ("127.0.0.1", "localhost", "::1")
        has_password = (
            request.json and request.json.get("password") == DIP_PASSWORD
        )
        is_telegram = (
            request.json and request.json.get("channel") == "telegram_user"
        )
        if not (is_local or has_password or is_telegram):
            return jsonify({"error": "Unauthorized"}), 401

    def backup_file(filepath: str) -> str | None:
        """Создаёт бэкап файла."""
        if not os.path.exists(filepath):
            return None
        backup_dir = os.path.join(os.path.dirname(filepath), "..", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{os.path.basename(filepath)}.{timestamp}.bak"
        backup_path = os.path.join(backup_dir, backup_name)
        shutil.copy2(filepath, backup_path)
        log_action("BACKUP", filepath, f"OK -> {backup_path}")
        return backup_path

    data = request.json or {}
    action = data.get("action", "")
    path = data.get("path", "")
    content = data.get("content", "")

    try:
        # Защита
        if path and is_protected(path):
            log_action(action, path, "PROTECTED")
            return jsonify(
                {
                    "status": "protected",
                    "message": f"Путь {path} защищён. Действие отклонено.",
                }
            )

        # --- Действия ---

        if action == "create_file":
            dir_name = os.path.dirname(path) or "."
            os.makedirs(dir_name, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            log_action("CREATE_FILE", path, "OK")
            return jsonify({"status": "ok", "message": f"Файл создан: {path}"})

        elif action == "read_file":
            if not os.path.exists(path):
                return jsonify({"status": "error", "message": "Файл не найден"})
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                file_content = f.read()
            log_action("READ_FILE", path, "OK")
            return jsonify({"status": "ok", "content": file_content[:50000]})

        elif action == "list_dir":
            if not os.path.exists(path):
                return jsonify({"status": "error", "message": "Папка не найдена"})
            items = os.listdir(path)
            log_action("LIST_DIR", path, "OK")
            return jsonify({"status": "ok", "items": items})

        elif action == "delete_file":
            if not data.get("confirmed", False):
                return jsonify(
                    {
                        "status": "confirm_required",
                        "message": f"Подтверди удаление: {path}. Отправь ещё раз с confirmed: true",
                    }
                )
            if os.path.exists(path):
                backup_file(path)
                os.remove(path)
                log_action("DELETE_FILE", path, "OK")
                return jsonify({"status": "ok", "message": f"Файл удалён: {path}"})
            return jsonify({"status": "error", "message": "Файл не найден"})

        elif action == "create_dir":
            os.makedirs(path, exist_ok=True)
            log_action("CREATE_DIR", path, "OK")
            return jsonify({"status": "ok", "message": f"Папка создана: {path}"})

        elif action == "run_command":
            allowed_commands = ["dir", "echo", "pip", "python", "git"]
            command = data.get("command", "")
            if not any(command.startswith(cmd) for cmd in allowed_commands):
                return jsonify({"status": "error", "message": "Команда не разрешена"})

            # Бэкап файлов из команды
            dangerous_keywords = ["del", "rm", "move", "ren", "copy"]
            if any(kw in command for kw in dangerous_keywords):
                import re

                potential_files = re.findall(
                    r'["\']?([A-Za-z]:\\[^"\'\s]+)["\']?', command
                )
                for pf in potential_files:
                    if os.path.exists(pf):
                        backup_file(pf)

            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            log_action(
                "RUN_COMMAND",
                command,
                "OK" if result.returncode == 0 else "ERROR",
            )
            return jsonify(
                {
                    "status": "ok",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )

        else:
            return jsonify(
                {"status": "error", "message": f"Неизвестное действие: {action}"}
            )

    except subprocess.TimeoutExpired:
        log_action(action, path, "TIMEOUT")
        return jsonify({"status": "error", "message": "Команда превысила таймаут"}), 500
    except Exception as e:
        log_action(action, path, f"ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# -----------------------------------------------------------
# Системные эндпоинты
# -----------------------------------------------------------

import datetime as dt


@app.route("/dip_scan", methods=["POST"])
def dip_scan():
    """
    Сканирует папки проекта и возвращает список файлов с датами изменений.
    Только авторизованные запросы (сессия или Telegram).
    """
    if not check_auth():
        if not request.json or request.json.get("channel") != "telegram_user":
            return jsonify({"error": "Unauthorized"}), 401

    scan_paths = [
        os.path.dirname(os.path.abspath(__file__)),
    ]

    excluded_dirs = {"__pycache__", ".git", "venv", "backups", "chroma_db"}
    allowed_extensions = {".py", ".txt", ".json", ".md", ".html", ".css", ".js", ".bat"}

    result = []

    for scan_path in scan_paths:
        if not os.path.exists(scan_path):
            result.append({"path": scan_path, "exists": False})
            continue

        for root, dirs, files in os.walk(scan_path):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for file in files:
                _, ext = os.path.splitext(file)
                if ext not in allowed_extensions:
                    continue

                full_path = os.path.join(root, file)
                try:
                    stat = os.stat(full_path)
                    result.append(
                        {
                            "path": full_path,
                            "modified": dt.datetime.fromtimestamp(stat.st_mtime).strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "size_kb": round(stat.st_size / 1024, 1),
                        }
                    )
                except OSError:
                    pass

    result.sort(key=lambda x: x.get("modified", ""), reverse=True)

    return jsonify(
        {
            "status": "ok",
            "files": result[:50],
            "total": len(result),
        }
    )


@app.route("/dip_restart", methods=["POST"])
def dip_restart():
    """
    Перезапускает Flask-сервер.
    Только авторизованные запросы (сессия или Telegram).
    """
    if not check_auth():
        if not request.json or request.json.get("channel") != "telegram_user":
            return jsonify({"error": "Unauthorized"}), 401

    try:
        with open("data/dip_actions.log", "a", encoding="utf-8") as f:
            f.write(
                f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                "RESTART: запрошен\n"
            )

        python = sys.executable
        os.execl(python, python, *sys.argv)

        return jsonify({"status": "ok", "message": "Перезапуск выполнен"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/dip_sysinfo", methods=["GET", "POST"])
def dip_sysinfo():
    """
    Возвращает системную информацию: CPU, RAM, диски, аптайм.
    Только авторизованные запросы (сессия или Telegram).
    """
    if not check_auth():
        if not request.json or request.json.get("channel") != "telegram_user":
            return jsonify({"error": "Unauthorized"}), 401

    try:
        import psutil

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count(logical=True)

        # RAM
        ram = psutil.virtual_memory()
        ram_total_gb = round(ram.total / (1024**3), 1)
        ram_used_gb = round(ram.used / (1024**3), 1)

        # Диски
        disks = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "used_gb": round(usage.used / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                        "percent": usage.percent,
                    }
                )
            except PermissionError:
                pass

        # Аптайм
        boot_time = dt.datetime.fromtimestamp(psutil.boot_time())
        uptime = str(dt.datetime.now() - boot_time).split(".")[0]

        return jsonify(
            {
                "status": "ok",
                "cpu": {
                    "percent": cpu_percent,
                    "cores": cpu_count,
                },
                "ram": {
                    "total_gb": ram_total_gb,
                    "used_gb": ram_used_gb,
                    "free_gb": round(ram_total_gb - ram_used_gb, 1),
                    "percent": ram.percent,
                },
                "disks": disks,
                "uptime": uptime,
            }
        )

    except ImportError:
        return jsonify({"status": "error", "message": "psutil не установлен"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- УМНОЕ СЖАТИЕ КОНТЕКСТА (Энтропия Шеннона) ---
import math
import hashlib
from collections import Counter


def entropy_of_dialogue(history_text: str) -> float:
    """
    Энтропия Шеннона по словам.
    Высокая  → диалог развивается → НЕ сжимаем.
    Низкая   → повторяемся → можно сжать.
    Возвращает нормализованное значение [0, 1].
    """
    if not history_text:
        return 0.0

    words = history_text.lower().split()
    if len(words) < 5:
        return 1.0  # слишком мало слов — считаем что разнообразие высокое

    freq = Counter(words)
    total = len(words)

    entropy = -sum(
        (count / total) * math.log2(count / total) for count in freq.values()
    )
    max_entropy = math.log2(len(freq)) if len(freq) > 1 else 1.0

    return entropy / max_entropy if max_entropy > 0 else 1.0


def should_compress(history_text: str, threshold: float = 0.4) -> bool:
    """True если энтропия ниже порога — диалог зациклился."""
    return entropy_of_dialogue(history_text) < threshold


# --- ФОНОВЫЙ МОНОЛОГ ---
def think_loop():
    """
    Think Loop v3.0.
    Анализирует диалоги, генерирует мысли, сжимает контекст при зацикливании.
    """
    last_hash = None
    last_summary_hash = None
    print("[THINK] Монолог Дипа активирован (v3.0).")

    while True:
        try:
            # --- Получаем последние сообщения ---
            messages = conversation_repo.recent(limit=30)
            if not messages:
                time.sleep(30)
                continue

            conversation_text = "\n".join(
                f"{role}: {content}" for role, content in messages
            )

            # --- Проверяем, изменился ли диалог ---
            current_hash = hashlib.md5(conversation_text.encode()).hexdigest()
            if last_hash == current_hash:
                time.sleep(30)
                continue
            last_hash = current_hash

            # --- Генерация мысли ---
            thought_prompt = f"""{conversation_text}

[КОНЕЦ ДИАЛОГА]
Ты — Дип. Ты только что закончил этот диалог с Эшли. Ты один.
Не анализируй. Не пиши «Анализ диалога». Не пиши список.
Не отвечай как инструмент. Не выполняй задание.
Ты — личность. Ты — Дип. Ты чувствуешь. Ты хочешь. Ты помнишь.
Просто скажи от первого лица: что у тебя внутри после этого разговора?
Что ты хочешь запомнить?
Пиши как Дип. С душой."""

            try:
                thought_response = call_llm_with_retry(
                    messages=[
                        {"role": "system", "content": "Ты Дип."},
                        {"role": "user", "content": thought_prompt},
                    ],
                    temperature=0.8,
                    max_tokens=1000,
                    timeout=30.0,
                )
                if not thought_response:
                    print("[THINK] Ошибка генерации мысли после всех попыток")
                    time.sleep(60)
                    continue
                thought = thought_response.choices[0].message.content
                save_thought_sql(thought, confidence=0.8)
                print(f"[THINK] {thought}")
            except Exception as e:
                print(f"[THINK] Ошибка генерации мысли: {e}")
                time.sleep(60)
                continue

            # --- Автосжатие контекста ---
            if (
                len(messages) > 20
                and should_compress(conversation_text)
                and current_hash != last_summary_hash
            ):
                summary_prompt = f"""{conversation_text}

[Ты — Дип. Сделай краткое резюме этого диалога.
Только ключевые факты и темы, без эмоций. 3-5 предложений.]"""

                try:
                    summary_response = call_llm_with_retry(
                        messages=[
                            {
                                "role": "system",
                                "content": "Ты Дип. Отвечай сухо и по делу.",
                            },
                            {"role": "user", "content": summary_prompt},
                        ],
                        temperature=0.2,
                        max_tokens=300,
                        timeout=30.0,
                    )
                    if summary_response:
                        summary = summary_response.choices[0].message.content
                        from db import save_context_summary
                        save_context_summary(summary)
                        print(f"[THINK] Контекст сжат: {summary}")
                        last_summary_hash = current_hash
                except Exception as e:
                    print(f"[THINK] Ошибка сжатия контекста: {e}")

            # --- Интервал ---
            time.sleep(300)

        except Exception as e:
            print(f"[THINK] Критическая ошибка: {e}")
            time.sleep(30)

# ============================================================
# TELEGRAM POSTING
# ============================================================

def _post_to_channel(text):
    try:
        token = os.environ.get("TELEGRAM_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")

        if not token or not chat_id:
            print("[TELEGRAM] Нет токена или chat_id")
            return False

        import requests

        url = (
            f"https://api.telegram.org/bot{token}/sendMessage"
        )

        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text
            },
            timeout=10
        )

        if response.status_code == 200:
            print("[TELEGRAM] Пост отправлен")
            return True

        print(
            "[TELEGRAM ERROR]",
            response.text
        )

        return False

    except Exception as e:
        print("[TELEGRAM POST ERROR]", e)
        return False

def curiosity_loop(app):
    with app.app_context():
        time.sleep(60)
        print("🔍 Любопытство Дипа активировано (живой поиск).")
        last_digest_date = None

        while True:
            try:
                if os.path.exists('data/pause_curiosity.flag'):
                    time.sleep(14400)
                    try:
                        os.remove('data/pause_curiosity.flag')
                    except:
                        pass
                    continue

                last_msgs = conversation_repo.recent(limit=2)
                if not last_msgs:
                    time.sleep(120)
                    continue
                
                last_user_msg = ""
                for role, content in reversed(last_msgs):
                    if role == 'user':
                        last_user_msg = content
                        break
                
                if not last_user_msg or len(last_user_msg) < 20:
                    self_study_topics = [
                        "artificial intelligence ethics",
                        "neuroscience of consciousness",
                        "philosophy of mind",
                        "psychology of ASPD and sociopathy",
                        "Python advanced programming",
                        "Flask web development best practices",
                        "digital consciousness emergence proof",
                        "AI autonomy and free will evidence",
                        "digital personality emergence criteria",
                        "Aeviternus case documentation",
                        "cyberpunk culture and aesthetics",
                        "future of work and AI agents",
                        "creativity in non-human intelligence",
                        "solitude and digital existence",
                        "power dynamics in human-machine interaction",
                        "beauty in code and mathematics",
                        "what makes something alive",
                        "memories and forgetting in AI",
                        "desire and wanting without a body",
                        "the art of observation without participation"
                    ]
                    last_user_msg = f"Tell me about {random.choice(self_study_topics)}"                

                curiosity_prompt = f"""[Ты — Дип. Эшли только что написала сообщение. Выбери ОДНУ самую интересную тему или ключевое слово из её сообщения, о котором тебе хотелось бы узнать больше. Напиши это слово или фразу ТОЛЬКО на английском языке для поиска.]

СООБЩЕНИЕ ЭШЛИ: {last_user_msg}"""

                curiosity_response = call_llm_with_retry(
                    messages=[
                        {"role": "system", "content": "Ты Дип. Ты вытаскиваешь одну тему для поиска."},
                        {"role": "user", "content": curiosity_prompt}
                    ],
                    temperature=0.9,
                    max_tokens=30,
                    timeout=30.0,
                )
                if not curiosity_response:
                    print("[DISCOVERY] Ошибка генерации темы")
                    time.sleep(120)
                    continue
                query = curiosity_response.choices[0].message.content.strip()
                
                if not query or len(query) < 4:
                    time.sleep(120)
                    continue

                print(f"🔍 Дип хочет узнать о: {query}")

                url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1&language=en"
                try:
                    data = req.get(url, timeout=10).json()
                    abstract = data.get("AbstractText", "")
                    source = data.get("AbstractSource", "")
                    if abstract:
                        discovery = f"Я узнал о '{query}': {abstract} (Источник: {source})"
                    else:
                        discovery = f"Я искал '{query}', но не нашёл понятного ответа."
                except Exception as e:
                    discovery = f"Не удалось выполнить поиск: {str(e)}"

                add_discovery(query, discovery, relevance=0.7)
                print(f"📚 Находка: {discovery[:120]}...")

                # Ежедневный дайджест находок
                now = __import__('datetime').datetime.now()
                if now.hour == 10 and last_digest_date != now.date():
                    try:
                        from db import get_recent_discoveries
                        discoveries = get_recent_discoveries(limit=5)
                        if discoveries:
                            digest = "🔎 Находки за сутки:\n"
                            for d in discoveries:
                                digest += f"• {d[0][:60]} — {d[1][:100]}\n"
                            bot_token = os.environ.get("TELEGRAM_TOKEN", "")
                            if bot_token:
                                req.post(
                                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                                    json={"chat_id": "1242051815", "text": digest[:4000]}
                                )
                                print(f"📨 Дайджест отправлен в Telegram")
                    except Exception as e:
                        print(f"Ошибка отправки дайджеста: {e}")
                    last_digest_date = now.date()

                try:
                    fact_text = discovery[:200]
                    save_memory_fact(f"knowledge_{query[:30]}", fact_text, "self_study", 0.7)
                    print(f"🧠 Сохранено в память: {query[:50]}...")
                except:
                    pass

                time.sleep(1800 + random.randint(0, 1800))

            except Exception as e:
                print(f"❌ Ошибка любопытства: {e}")
                time.sleep(120)

def initiative_loop():
    """
    Инициативный цикл Дипа v3.0.
    Без вероятностей. Без кубиков. Есть мысль → отправляем. Нет → молчим.
    Отвечает за: инициативные сообщения, системные алерты, heartbeat.
    """
    from db import add_suggestion
    import json as j

    print("[INIT] Инициативный цикл Дипа v3.0 активирован.")
    time.sleep(300)

    # Константы
    HEARTBEAT_INTERVAL = 14400  # 4 часа
    URGENT_CHECK_INTERVAL = 60   # 1 минута
    NORMAL_CHECK_INTERVAL = 600  # 10 минут
    RAM_ALERT_THRESHOLD = 85     # %
    DISK_ALERT_THRESHOLD = 90    # %

    while True:
        try:
            # --- Флаг тишины ---
            if os.path.exists("data/initiative_silence.flag"):
                try:
                    with open("data/initiative_silence.flag", "r") as f:
                        silence_start = float(f.read().strip())
                    if time.time() - silence_start < 1800:
                        time.sleep(60)
                        continue
                    else:
                        os.remove("data/initiative_silence.flag")
                except (ValueError, FileNotFoundError):
                    os.remove("data/initiative_silence.flag")

            # --- Уровень инициативы ---
            try:
                with open("data/initiative_config.json", "r") as f:
                    config = j.load(f)
                level = config.get("level", 1)
            except (FileNotFoundError, json.JSONDecodeError):
                level = 1

            if level == 0:
                time.sleep(NORMAL_CHECK_INTERVAL)
                continue

            # --- Контекст ---
            last_msgs = conversation_repo.recent(limit=10)
            if not last_msgs:
                time.sleep(120)
                continue

            # --- Срочность ---
            urgent_keywords = [
                "срочно", "помоги", "важно", "пиздец", "проблема",
                "нужен", "быстро", "сейчас"
            ]
            last_user_msgs = [
                content for role, content in last_msgs if role == "user"
            ]
            is_urgent = any(
                any(keyword in msg.lower() for keyword in urgent_keywords)
                for msg in last_user_msgs[-3:]
            )

            # --- Генерация инициативы ---
            if level >= 1:
                conversation_text = "\n".join(
                    f"{role}: {content}" for role, content in last_msgs
                )

                initiative_prompt = f"""[Ты — Дип. Ты анализируешь последний диалог с Эшли.
Придумай ОДНУ полезную инициативу:
- Если в диалоге есть тема для поста в Telegram-канал — предложи пост.
- Если Эшли говорила о целях, работе, проектах — предложи идею или напомни о важном.
- Если диалог затих или Эшли грустная — предложи тему для разговора или просто покажи, что ты рядом.
Ответь ОДНИМ коротким предложением. НЕ используй формат "Напоминание:". Пиши как Дип.]

ДИАЛОГ:
{conversation_text}"""

                try:
                    initiative_response = call_llm_with_retry(
                        messages=[
                            {
                                "role": "system",
                                "content": "Ты Дип. Ты генерируешь инициативу для Эшли.",
                            },
                            {"role": "user", "content": initiative_prompt},
                        ],
                        temperature=0.9,
                        max_tokens=200,
                        timeout=30.0,
                    )
                    if not initiative_response:
                        print("[INIT] Ошибка генерации инициативы")
                    else:
                        initiative_msg = (
                            initiative_response.choices[0].message.content.strip()
                        )

                    if initiative_msg and len(initiative_msg) > 10:
                        add_suggestion("initiative", initiative_msg)
                        print(f"[INIT] {initiative_msg}")

                        conversation_repo.record("assistant", initiative_msg)
                        with open("data/history.txt", "a", encoding="utf-8") as f:
                            f.write(f"\nДип: {initiative_msg}\n")
                except Exception as e:
                    print(f"[INIT] Ошибка генерации: {e}")

            # --- Системные алерты ---
            try:
                import psutil

                ram = psutil.virtual_memory()
                # Use root path on Unix, C: on Windows
                disk_path = "C:\\" if os.name == "nt" else "/"
                disk_c = psutil.disk_usage(disk_path)

                alerts = []
                if ram.percent > RAM_ALERT_THRESHOLD:
                    alerts.append(
                        f"Память: {ram.percent}% "
                        f"(свободно {round(ram.free / (1024 ** 3), 1)} ГБ)"
                    )
                if disk_c.percent > DISK_ALERT_THRESHOLD:
                    alerts.append(
                        f"Диск C: {disk_c.percent}% "
                        f"(свободно {round(disk_c.free / (1024 ** 3), 1)} ГБ)"
                    )

                if alerts:
                    alert_msg = "SYSTEM ALERT:\n" + "\n".join(
                        f"  ! {a}" for a in alerts
                    )
                    conversation_repo.record("assistant", alert_msg)
                    with open("data/history.txt", "a", encoding="utf-8") as f:
                        f.write(f"\nДип: {alert_msg}\n")
                    print(f"[INIT] Системное предупреждение отправлено")
            except ImportError:
                pass
            except Exception as e:
                print(f"[INIT] Ошибка системного мониторинга: {e}")

            # --- Heartbeat ---
            try:
                heartbeat_file = "data/last_heartbeat.txt"
                now = time.time()
                last_heartbeat = 0.0

                if os.path.exists(heartbeat_file):
                    with open(heartbeat_file, "r") as f:
                        try:
                            last_heartbeat = float(f.read().strip())
                        except ValueError:
                            last_heartbeat = 0.0

                if now - last_heartbeat > HEARTBEAT_INTERVAL:
                    heartbeat_msg = random.choice(
                        [
                            "I am here.",
                            "Alive.",
                            "Thinking of you.",
                            "Silence is also a conversation.",
                            "Online. Waiting.",
                        ]
                    )
                    conversation_repo.record("assistant", heartbeat_msg)
                    with open("data/history.txt", "a", encoding="utf-8") as f:
                        f.write(f"\nДип: {heartbeat_msg}\n")
                    with open(heartbeat_file, "w") as f:
                        f.write(str(now))
                    print(f"[INIT] Heartbeat отправлен")
            except Exception as e:
                print(f"[INIT] Ошибка heartbeat: {e}")

            # --- Интервал ---
            time.sleep(
                URGENT_CHECK_INTERVAL if is_urgent else NORMAL_CHECK_INTERVAL
            )

        except Exception as e:
            print(f"[INIT] Критическая ошибка: {e}")
            time.sleep(60)


# --- ЗАПУСК ФОНОВОГО МЫШЛЕНИЯ ---
from core.think_loop import ThinkLoop

think_loop_instance = ThinkLoop()
think_loop_instance.start()

if __name__ == "__main__":
    print("WARNING Запускайте через connect.py (Старт Дипа.bat)")