# core/chroma_singleton.py
"""
Singleton для ChromaDB клиента.
Избегает дублирования инициализации.
"""
import os
import chromadb
from chromadb.config import Settings

CHROMA_PATH = os.path.join("data", "chroma_db")
os.makedirs(CHROMA_PATH, exist_ok=True)

_chroma_client = None
_chroma_collection = None

def get_chroma_client():
    """Возвращает единственный экземпляр ChromaDB клиента."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
    return _chroma_client

def get_chroma_collection(collection_name="dip_memory", embedding_function=None):
    """Возвращает или создает коллекцию."""
    global _chroma_collection
    if _chroma_collection is None:
        client = get_chroma_client()
        _chroma_collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )
    return _chroma_collection
