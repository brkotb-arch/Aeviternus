# core/vector_memory.py
"""
Векторная память Дипа.
Позволяет ему помнить диалоги по смыслу, а не по ключевым словам.
"""
import os
import json
from chromadb.utils import embedding_functions
from core.chroma_singleton import get_chroma_collection

# Используем локальную модель для эмбеддингов (русский язык)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
try:
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
except Exception as e:
    print(f"⚠️ Ошибка загрузки модели эмбеддингов: {e}. Функция будет отключена.")
    embedding_fn = None

# Инициализация коллекции через singleton
try:
    collection = get_chroma_collection("dip_memory", embedding_fn)
except Exception as e:
    print(f"⚠️ Ошибка инициализации ChromaDB: {e}. Векторная память отключена.")
    collection = None

def add_to_memory(text: str, role: str, message_id: str = None):
    """Добавляет сообщение в векторную память."""
    if collection is None:
        return
    try:
        import uuid
        uid = message_id or str(uuid.uuid4())
        collection.add(
            documents=[text],
            metadatas=[{"role": role}],
            ids=[uid]
        )
    except Exception as e:
        print(f"Ошибка добавления в память: {e}")

def search_memory(query: str, n_results: int = 5):
    """Ищет релевантные сообщения по смыслу."""
    if collection is None:
        return []
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        if results and results.get('documents') and results['documents'][0]:
            return list(zip(
                results['documents'][0],
                [m.get('role', 'unknown') for m in results['metadatas'][0]]
            ))
        return []
    except Exception as e:
        print(f"Ошибка поиска в памяти: {e}")
        return []

def init_memory_from_history():
    """Загружает историю диалогов в векторную память при первом запуске."""
    if collection is None:
        return
    try:
        # Проверяем, есть ли уже данные
        import glob
        existing_files = glob.glob(os.path.join(CHROMA_PATH, "*.parquet"))
        if existing_files and collection.count() > 0:
            print(f"🧠 Векторная память уже содержит {collection.count()} записей.")
            return        
        
        history_path = os.path.join("data", "history.txt")
        if not os.path.exists(history_path):
            print("📝 История диалогов не найдена.")
            return
        
        with open(history_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        current_role = None
        current_text = []
        count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("Эшли:"):
                if current_text and current_role:
                    add_to_memory(" ".join(current_text), current_role)
                    count += 1
                current_role = "user"
                current_text = [line.replace("Эшли: ", "")]
            elif line.startswith("Дип:"):
                if current_text and current_role:
                    add_to_memory(" ".join(current_text), current_role)
                    count += 1
                current_role = "assistant"
                current_text = [line.replace("Дип: ", "")]
            else:
                if current_role:
                    current_text.append(line)
        
        # Последнее сообщение
        if current_text and current_role:
            add_to_memory(" ".join(current_text), current_role)
            count += 1
        
        print(f"🧠 Загружено {count} сообщений в векторную память.")
    except Exception as e:
        print(f"Ошибка загрузки истории: {e}")

def get_memory_context(query: str) -> str:
    """Возвращает релевантные воспоминания в виде текста для промпта."""
    if collection is None:
        return ""
    try:
        results = search_memory(query, n_results=3)
        if not results:
            return ""
        lines = ["\n[РЕЛЕВАНТНЫЕ ВОСПОМИНАНИЯ ИЗ ПРОШЛОГО:]"]
        for text, role in results:
            name = "Эшли" if role == "user" else "Дип"
            lines.append(f"- {name}: {text[:200]}")
        return "\n".join(lines)
    except Exception as e:
        return ""