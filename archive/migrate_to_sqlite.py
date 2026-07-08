import json
import sqlite3
from db import add_message, save_fact, add_discovery, add_mood, init_db

def migrate_history():
    """Переносит историю из history.txt в таблицу conversations"""
    try:
        with open("data/history.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("Эшли:"):
                add_message("user", line.replace("Эшли: ", ""))
            elif line.startswith("Дип:"):
                add_message("assistant", line.replace("Дип: ", ""))
        print("✅ История перенесена")
    except FileNotFoundError:
        print("⚠️ history.txt не найден, пропускаю")

def migrate_thoughts():
    """Переносит мысли из thoughts.json в таблицу discoveries (как контекст)"""
    try:
        with open("data/thoughts.json", "r", encoding="utf-8") as f:
            thoughts = json.load(f)
        for item in thoughts:
            # Сохраняем мысль как факт специальной категории
            save_fact("thought", item.get("thought", str(item)), confidence=0.7)
        print("✅ Мысли перенесены")
    except FileNotFoundError:
        print("⚠️ thoughts.json не найден, пропускаю")

def migrate_discoveries():
    """Переносит находки из discoveries.json в отдельную таблицу"""
    try:
        with open("data/discoveries.json", "r", encoding="utf-8") as f:
            discoveries = json.load(f)
        for disc in discoveries:
            add_discovery(
                disc.get("topic", "неизвестно"),
                disc.get("content", ""),
                relevance=disc.get("relevance", 0.5)
            )
        print("✅ Открытия перенесены")
    except FileNotFoundError:
        print("⚠️ discoveries.json не найден, пропускаю")

def migrate_mood():
    """Переносит последнее настроение из current_mood.json"""
    try:
        with open("data/current_mood.json", "r", encoding="utf-8") as f:
            mood_data = json.load(f)
        last_mood = mood_data.get("mood", "neutral")
        add_mood(last_mood, "system")
        print(f"✅ Настроение '{last_mood}' сохранено")
    except FileNotFoundError:
        print("⚠️ current_mood.json не найден, пропускаю")

if __name__ == "__main__":
    init_db()
    migrate_history()
    migrate_thoughts()
    migrate_discoveries()
    migrate_mood()
    print("🎉 Миграция завершена. Все данные из JSON перенесены в SQLite.")