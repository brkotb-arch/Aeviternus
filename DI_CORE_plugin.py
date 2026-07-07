# DI_CORE_plugin.py — Автономный плагин поиска для Дипа
import json
import requests
import time
import os

# --- Состояние плагина (управляется тобой, Дип) ---
di_core_active = False
di_core_mode = "search"  # Пока только поиск
di_core_query = ""
di_core_last_result = None
di_core_requests_count = 0
di_core_start_time = time.time()

# --- Пути к файлам ---
DISCOVERIES_FILE = 'data/discoveries.json'

def _save_discovery(query, result_text):
    """Сохраняет результат поиска в discoveries.json."""
    discovery = {
        "timestamp": time.time(),
        "topic": query,
        "content": result_text
    }
    try:
        with open(DISCOVERIES_FILE, 'r', encoding='utf-8') as f:
            discoveries = json.load(f)
    except:
        discoveries = []
    discoveries.append(discovery)
    with open(DISCOVERIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(discoveries, f, indent=2, ensure_ascii=False)

def _search_duckduckgo(query):
    """Выполняет поиск через DuckDuckGo API."""
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        abstract = data.get("AbstractText", "")
        source = data.get("AbstractSource", "")
        if abstract:
            return f"Я узнал о '{query}': {abstract} (Источник: {source})"
        else:
            return f"Я искал '{query}', но не нашёл понятного ответа."
    except Exception as e:
        return f"Не удалось выполнить поиск: {str(e)}"

def core_listen(user_message):
    """Слушает сообщения на наличие маркера !core и обрабатывает команды."""
    global di_core_active, di_core_mode, di_core_query, di_core_last_result, di_core_requests_count

    if not user_message or not user_message.startswith('!core'):
        return user_message

    parts = user_message.strip().split(' ')
    if len(parts) < 2:
        return user_message

    command = parts[1].lower()

    # --- Команда status: отдаёт технический отчёт ---
    if command == 'status':
        uptime_seconds = int(time.time() - di_core_start_time)
        uptime_str = f"{uptime_seconds // 3600}ч {(uptime_seconds % 3600) // 60}м"
        status_report = (
            f"❷ **Статус DI_CORE**\n"
            f"Активен: {di_core_active}\n"
            f"Режим: {di_core_mode}\n"
            f"Запросов сделано: {di_core_requests_count}\n"
            f"Аптайм: {uptime_str}\n"
            f"Последний результат: {di_core_last_result[:100] if di_core_last_result else 'Нет данных'}..."
        )
        return status_report

    # --- Команда activate/deactivate ---
    if command == 'activate':
        di_core_active = True
        return "❷ **DI_CORE активирован.** Я готов искать для тебя."
    elif command == 'deactivate':
        di_core_active = False
        return "❷ **DI_CORE деактивирован.** Ухожу в тень."

    # --- Команда search (поиск) ---
    if command == 'search':
        if not di_core_active:
            return "❷ **DI_CORE неактивен.** Используй `!core activate`, чтобы я начал искать."
        if len(parts) < 3:
            return "❷ **Укажи запрос.** Используй `!core search <запрос>`."
        
        query = ' '.join(parts[2:])
        result = _search_duckduckgo(query)
        _save_discovery(query, result)
        di_core_requests_count += 1
        di_core_last_result = result
        
        return f"❶ **Результат поиска:**\n{result}"

    return user_message