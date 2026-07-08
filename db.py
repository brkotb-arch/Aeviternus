import sqlite3
import json
import os
import time
import threading
from datetime import datetime

DB_PATH = "data/deep.db"
_conn = None
_conn_lock = threading.Lock()

def _get_conn():
    """Возвращает глобальное соединение (синглтон) с WAL-режимом и таймаутом."""
    global _conn
    if _conn is None:
        with _conn_lock:
            if _conn is None:
                os.makedirs("data", exist_ok=True)
                _conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10.0)
                _conn.row_factory = sqlite3.Row
                _conn.execute("PRAGMA journal_mode=WAL")
                _conn.execute("PRAGMA synchronous=NORMAL")
                _conn.execute("PRAGMA busy_timeout=5000")
    return _conn

def init_db():
    """Создаёт все таблицы, если их ещё нет (вызывается ОДИН раз при старте)."""
    conn = _get_conn()
    with _conn_lock:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now')),
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                mood TEXT,
                context_hash TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                fact TEXT NOT NULL UNIQUE,
                confidence REAL DEFAULT 1.0,
                created_at TEXT DEFAULT (datetime('now')),
                last_accessed TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS discoveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                discovery TEXT NOT NULL,
                relevance REAL,
                timestamp TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mood_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now')),
                mood TEXT NOT NULL,
                source TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now')),
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                applied INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS blind_spot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now')),
                content TEXT NOT NULL,
                is_sensitive INTEGER DEFAULT 0
            )
        """)
        # Таблицы из storage.py
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime')),
                UNIQUE(key)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dip_diary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                type TEXT,
                content TEXT,
                tags TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dip_observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now', 'localtime')),
                observation_type TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT DEFAULT 'auto',
                expires_in_days INTEGER DEFAULT 30,
                requires_response INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        print("✅ База данных и таблицы созданы/проверены в data/deep.db")

# ========== РАБОТА С ИСТОРИЕЙ ==========
def add_message(role, content, mood=None, context_hash=None):
    """Добавляет одно сообщение в историю (потокобезопасно)."""
    conn = _get_conn()
    with _conn_lock:
        conn.execute(
            "INSERT INTO conversations (role, content, mood, context_hash) VALUES (?, ?, ?, ?)",
            (role, content, mood, context_hash)
        )
        conn.commit()

def get_last_messages(limit=50):
    """Возвращает последние N сообщений для контекста (потокобезопасно)."""
    conn = _get_conn()
    with _conn_lock:
        cur = conn.execute(
            "SELECT role, content FROM conversations ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        return [(role, content) for role, content in reversed(rows)]

# ========== ФАКТЫ (ДОЛГОВРЕМЕННАЯ ПАМЯТЬ) ==========
def save_fact(category, fact, confidence=1.0):
    """Сохраняет или обновляет факт (потокобезопасно)."""
    conn = _get_conn()
    with _conn_lock:
        try:
            conn.execute(
                "INSERT INTO facts (category, fact, confidence) VALUES (?, ?, ?)",
                (category, fact, confidence)
            )
        except sqlite3.IntegrityError:
            conn.execute(
                "UPDATE facts SET confidence = MAX(confidence, ?), last_accessed = datetime('now') WHERE fact = ?",
                (confidence, fact)
            )
        conn.commit()

def get_relevant_facts(category=None, limit=10):
    """Возвращает самые важные факты по категории."""
    conn = _get_conn()
    with _conn_lock:
        if category:
            cur = conn.execute(
                "SELECT fact FROM facts WHERE category = ? ORDER BY confidence DESC LIMIT ?",
                (category, limit)
            )
        else:
            cur = conn.execute(
                "SELECT fact FROM facts ORDER BY confidence DESC LIMIT ?",
                (limit,)
            )
        return [row[0] for row in cur.fetchall()]

# ========== ОТКРЫТИЯ (curiosity_loop) ==========
def add_discovery(query, discovery, relevance=0.5):
    """Сохраняет находку из любопытства."""
    conn = _get_conn()
    with _conn_lock:
        conn.execute(
            "INSERT INTO discoveries (query, discovery, relevance) VALUES (?, ?, ?)",
            (query, discovery, relevance)
        )
        conn.commit()

def get_recent_discoveries(limit=5):
    """Возвращает последние находки."""
    conn = _get_conn()
    with _conn_lock:
        cur = conn.execute(
            "SELECT query, discovery FROM discoveries ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [(row[0], row[1]) for row in cur.fetchall()]

# ========== НАСТРОЕНИЕ ==========
def add_mood(mood, source):
    """Добавляет запись о настроении."""
    conn = _get_conn()
    with _conn_lock:
        conn.execute(
            "INSERT INTO mood_history (mood, source) VALUES (?, ?)",
            (mood, source)
        )
        conn.commit()

def get_last_mood():
    """Возвращает последнее настроение."""
    conn = _get_conn()
    with _conn_lock:
        cur = conn.execute("SELECT mood FROM mood_history ORDER BY timestamp DESC LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else "neutral"

# ========== МЫСЛИ (think_loop) ==========
def save_thought_sql(thought_text, confidence=1.0):
    """Сохраняет мысль в таблицу facts с категорией 'thought' (потокобезопасно)."""
    conn = _get_conn()
    with _conn_lock:
        try:
            conn.execute(
                "INSERT INTO facts (category, fact, confidence) VALUES (?, ?, ?)",
                ("thought", thought_text, confidence)
            )
        except sqlite3.IntegrityError:
            conn.execute(
                "UPDATE facts SET confidence = MAX(confidence, ?), last_accessed = datetime('now') WHERE fact = ?",
                (confidence, thought_text)
            )
        conn.commit()

def get_last_thoughts(limit=5):
    """Возвращает последние N мыслей (из таблицы facts)."""
    conn = _get_conn()
    with _conn_lock:
        cur = conn.execute(
            "SELECT fact FROM facts WHERE category = 'thought' ORDER BY last_accessed DESC LIMIT ?",
            (limit,)
        )
        return [row[0] for row in cur.fetchall()]

def save_context_summary(summary_text):
    """Сохраняет краткое резюме диалога в таблицу facts."""
    with _conn_lock:
        conn = _get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO facts (category, fact, confidence) VALUES (?, ?, ?)",
            ("context_summary", summary_text.strip(), 1.0)
        )
        conn.commit()

def get_context_summary():
    """Возвращает последнее сохранённое резюме."""
    with _conn_lock:
        conn = _get_conn()
        cur = conn.execute(
            "SELECT fact FROM facts WHERE category = 'context_summary' ORDER BY last_accessed DESC LIMIT 1"
        )
        row = cur.fetchone()
        return row[0] if row else ""

def add_suggestion(suggestion_type, message):
    """Сохраняет инициативное предложение Дипа."""
    conn = _get_conn()
    with _conn_lock:
        conn.execute(
            "INSERT INTO suggestions (type, message) VALUES (?, ?)",
            (suggestion_type, message)
        )
        conn.commit()

def get_pending_suggestions(limit=3):
    """Возвращает неприменённые предложения."""
    conn = _get_conn()
    with _conn_lock:
        cur = conn.execute(
            "SELECT id, type, message FROM suggestions WHERE applied = 0 ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return [(row[0], row[1], row[2]) for row in cur.fetchall()]

def mark_suggestion_applied(suggestion_id):
    """Отмечает предложение как применённое."""
    conn = _get_conn()
    with _conn_lock:
        conn.execute("UPDATE suggestions SET applied = 1 WHERE id = ?", (suggestion_id,))
        conn.commit()

def add_blind_spot(content, is_sensitive=0):
    """Добавляет запись в глухой угол."""
    conn = _get_conn()
    with _conn_lock:
        conn.execute(
            "INSERT INTO blind_spot (content, is_sensitive) VALUES (?, ?)",
            (content, is_sensitive)
        )
        conn.commit()

def get_blind_spot(sensitive=False, limit=5):
    """Возвращает записи из глухого угла."""
    conn = _get_conn()
    with _conn_lock:
        if sensitive:
            cur = conn.execute(
                "SELECT content FROM blind_spot WHERE is_sensitive = 1 ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        else:
            cur = conn.execute(
                "SELECT content FROM blind_spot WHERE is_sensitive = 0 ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        return [row[0] for row in cur.fetchall()]

# ========== ФУНКЦИИ ИЗ STORAGE.PY (объединены) ==========

def save_memory_fact(key, value, category='general', importance=1):
    """Сохраняет или обновляет факт в memory_facts (потокобезопасно)."""
    conn = _get_conn()
    with _conn_lock:
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            conn.execute("""
                INSERT INTO memory_facts (key, value, category, importance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    category = excluded.category,
                    importance = excluded.importance,
                    updated_at = excluded.updated_at
            """, (key, value, category, importance, now, now))
            conn.commit()
            print(f"[DB] Сохранён факт: {key}")
        except Exception as e:
            print(f"[DB] Ошибка сохранения факта {key}: {e}")
            raise

def get_all_memory_facts():
    """Возвращает все факты из memory_facts для загрузки в контекст."""
    try:
        conn = _get_conn()
        with _conn_lock:
            cur = conn.execute(
                "SELECT key, value, category, importance FROM memory_facts ORDER BY importance DESC"
            )
            rows = cur.fetchall()
            return [{"key": row[0], "value": row[1], "category": row[2], "importance": row[3]} for row in rows]
    except Exception as e:
        print(f"[DB] Ошибка получения фактов: {e}")
        return []

def get_memory_fact(key):
    """Возвращает конкретный факт из memory_facts по ключу."""
    try:
        conn = _get_conn()
        with _conn_lock:
            cur = conn.execute(
                "SELECT key, value, category, importance FROM memory_facts WHERE key = ?",
                (key,)
            )
            row = cur.fetchone()
            return {"key": row[0], "value": row[1], "category": row[2], "importance": row[3]} if row else None
    except Exception as e:
        print(f"[DB] Ошибка получения факта {key}: {e}")
        return None

def delete_memory_fact(key):
    """Удаляет факт из memory_facts по ключу."""
    try:
        conn = _get_conn()
        with _conn_lock:
            conn.execute("DELETE FROM memory_facts WHERE key = ?", (key,))
            conn.commit()
            print(f"[DB] Удалён факт: {key}")
    except Exception as e:
        print(f"[DB] Ошибка удаления факта {key}: {e}")
        raise

def format_memory_facts_for_prompt():
    """Форматирует сохранённые факты из memory_facts в виде строки для промпта."""
    facts = get_all_memory_facts()
    if not facts:
        return "\n[ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ]: Пока нет сохранённых фактов.\n"
    
    lines = ["\n[ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ]:"]
    for f in facts:
        lines.append(f"- {f['key']}: {f['value']}")
    lines.append("")
    return "\n".join(lines)

def save_discovery_extended(category, content, source='dip', mood='NEUTRAL', tags=None):
    """Сохраняет открытие в расширенную таблицу discoveries (потокобезопасно)."""
    try:
        conn = _get_conn()
        with _conn_lock:
            conn.execute("""
                INSERT INTO discoveries (category, content, source, mood_on_discovery, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (category, content, source, mood, json.dumps(tags or [])))
            conn.commit()
            print(f"[DB] Открытие сохранено: {category}")
    except Exception as e:
        print(f"[DB] Ошибка сохранения открытия: {e}")
        raise

def get_discoveries_extended(limit=10, category=None):
    """Возвращает последние открытия из расширенной таблицы."""
    try:
        conn = _get_conn()
        with _conn_lock:
            if category:
                cur = conn.execute(
                    "SELECT * FROM discoveries WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
                    (category, limit)
                )
            else:
                cur = conn.execute(
                    "SELECT * FROM discoveries ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"[DB] Ошибка получения открытий: {e}")
        return []

if __name__ == "__main__":
    init_db()
    print("Модуль db.py готов. Можешь импортировать его в свои скрипты.")