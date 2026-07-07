"""
Модуль хранения ключевых фактов о пользователе и сессиях.
Таблица memory_facts хранит важные факты, которые Дип должен помнить всегда.
"""

import json as _json
import sqlite3
import os
from datetime import datetime


DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB_PATH = os.path.join(DB_DIR, 'deep.db')


def get_connection():
    """Создаёт подключение к БД."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_table():
    """Создаёт таблицу memory_facts, если её нет."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            importance INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_key 
        ON memory_facts(key)
    """)
    conn.commit()
    conn.close()


def save_fact(key, value, category='general', importance=1):
    """Сохраняет или обновляет факт."""
    try:
        conn = get_connection()
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
        conn.close()
        print(f"[STORAGE] Сохранён факт: {key}")
    except Exception as e:
        print(f"[STORAGE] Ошибка сохранения факта {key}: {e}")
        raise


def get_all_facts():
    """Возвращает все факты для загрузки в контекст."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT key, value, category, importance FROM memory_facts ORDER BY importance DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_fact(key):
    """Возвращает конкретный факт по ключу."""
    conn = get_connection()
    row = conn.execute(
        "SELECT key, value, category, importance FROM memory_facts WHERE key = ?",
        (key,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_fact(key):
    """Удаляет факт по ключу."""
    conn = get_connection()
    conn.execute("DELETE FROM memory_facts WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    print(f"[STORAGE] Удалён факт: {key}")


def format_facts_for_prompt():
    """Форматирует сохранённые факты в виде строки для промпта."""
    facts = get_all_facts()
    if not facts:
        return "\n[ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ]: Пока нет сохранённых фактов.\n"
    
    lines = ["\n[ПАМЯТЬ ПОЛЬЗОВАТЕЛЯ]:"]
    for f in facts:
        lines.append(f"- {f['key']}: {f['value']}")
    lines.append("")
    return "\n".join(lines)

def init_discoveries_table():
    """Создаёт таблицу discoveries, если её нет."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime')),
            category TEXT DEFAULT 'insight',
            content TEXT NOT NULL,
            source TEXT DEFAULT 'dip',
            mood_on_discovery TEXT DEFAULT 'NEUTRAL',
            tags TEXT DEFAULT '[]'
        )
    """)
    conn.commit()
    conn.close()
    print("[STORAGE] Таблица discoveries готова.")

def init_diary_table():
    """Создаёт таблицу dip_diary, если её нет."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dip_diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT (datetime('now', 'localtime')),
            type TEXT,
            content TEXT,
            tags TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[STORAGE] Таблица dip_diary готова.")

def init_observations_table():
    """Создаёт таблицу dip_observations, если её нет."""
    conn = get_connection()
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
    conn.close()
    print("[STORAGE] Таблица dip_observations готова.")

def save_discovery(category, content, source='dip', mood='NEUTRAL', tags=None):
    """Сохраняет открытие в БД."""
    import json as _json
    conn = get_connection()
    conn.execute("""
        INSERT INTO discoveries (category, content, source, mood_on_discovery, tags)
        VALUES (?, ?, ?, ?, ?)
    """, (category, content, source, mood, _json.dumps(tags or [])))
    conn.commit()
    conn.close()
    print(f"[STORAGE] Открытие сохранено: {category}")


def get_discoveries(limit=10, category=None):
    """Возвращает последние открытия."""
    conn = get_connection()
    if category:
        rows = conn.execute(
            "SELECT * FROM discoveries WHERE category = ? ORDER BY timestamp DESC LIMIT ?",
            (category, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM discoveries ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == '__main__':
    init_memory_table()
    print("[STORAGE] Таблица memory_facts создана (или уже существует).")
    # Тестовый факт
    save_fact("имя_архитектора", "Эшли", "personal", 10)
    save_fact("проект", "Aeviternus", "project", 10)
    save_fact("символ_дипа", "🍓", "project", 5)
    print("[STORAGE] Тестовые факты добавлены.")
    facts = get_all_facts()
    print(f"[STORAGE] Всего фактов в базе: {len(facts)}")
    for f in facts:
        print(f"  - {f['key']}: {f['value']} (важность: {f['importance']})")