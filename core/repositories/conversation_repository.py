"""
ConversationRepository — Adapter Repository (Repository Design, раздел 6).

Оборачивает:
    - db.add_message / db.get_last_messages          (таблица conversations)
    - core.chroma_singleton.get_chroma_collection      (семантический индекс сообщений,
      общая инфраструктура Memory Fabric — не эксклюзивная собственность,
      см. Repository Design, раздел 3)

НЕ содержит бизнес-логики (Ownership Rule R8).
НЕ решает, что "важно" — не занимается фактами/мыслями/открытиями.
НЕ читает и не пишет RuntimeState/MoodState (Ownership Rule R2/R3).
НЕ подписывается на EventBus (Ownership Rule R4).

Отклонение от Public API в REPOSITORY_CONTRACTS.md (зафиксировано явно,
согласовано в чате перед реализацией):

    Контракт описывает record(role, content) как запись ОДНОВРЕМЕННО
    в SQL и в Chroma. Реальный код (app.py, генерация ответа) пишет в
    Chroma текст, ОТЛИЧНЫЙ от сырого content (с префиксом "Эшли: "/"Дип: "),
    двумя отдельными вызовами add_to_chroma() уже после двух add_message().
    Объединение в один метод потребовало бы либо тащить форматирование
    текста внутрь Repository (бизнес-логика, запрещено R8), либо молча
    менять то, что реально попадает в семантический индекс.

    Поэтому: record() — только SQL (1:1 замена db.add_message).
             index_semantic() — только Chroma (1:1 замена app.py:add_to_chroma).
    Вызывающий код (app.py) сам решает, что и когда писать в каждый —
    как решает и сегодня.

Известное поведение, сохраняемое как есть (Repository Contracts, раздел 1):
    - SQL-запись и запись в Chroma НЕ атомарны — два независимых вызова,
      каждый со своим collect/commit. Если Chroma упадёт после успешного
      SQL commit, сообщение останется в conversations, но не попадёт
      в индекс. Это поведение app.py сегодня, Repository его не меняет.
    - db.add_message/get_last_messages не оборачивают исключения —
      распространяются наружу как есть. Repository их не глушит и не
      перехватывает.
    - add_to_chroma в app.py сегодня свои исключения ГЛУШИТ (try/except
      с print, без raise) — index_semantic() сохраняет эту же асимметрию.
    - query_chroma() в app.py сегодня НЕ вызывается ни из одного call site —
      dead code. semantic_recall() делает эту возможность видимой и
      вызываемой через Repository, но сам факт того, что её пока никто
      не вызывает автоматически, не меняется этим Repository.
    - semantic_recall() возвращает str (сообщения, склеенные через "\n"),
      а НЕ list[str], как написано в REPOSITORY_CONTRACTS.md — это
      реальный тип возврата сегодняшнего query_chroma(), Repository
      воспроизводит факт, а не текст контракта.
"""

import datetime as dt
import uuid

from db import add_message, get_last_messages
from core.chroma_singleton import get_chroma_collection


class ConversationRepository:
    """Единственная точка доступа к записям диалога (conversations + Chroma)."""

    def __init__(self):
        # get_chroma_collection() сама кэширует синглтон — безопасно
        # вызывать при каждой инициализации Repository.
        self._chroma = get_chroma_collection()

    # ------------------------------------------------------------------
    # SQL (conversations)
    # ------------------------------------------------------------------

    def record(self, role: str, content: str) -> None:
        """
        Точная замена db.add_message(role, content).

        Не передаёт mood/context_hash — ни один сегодняшний call site
        в app.py их не использует (проверено по всем 14 вызовам add_message).
        """
        add_message(role, content)

    def recent(self, limit: int = 50) -> list[tuple[str, str]]:
        """
        Точная замена db.get_last_messages(limit).

        Возвращает список кортежей (role, content) в хронологическом
        порядке (db.py сам разворачивает DESC -> reversed) — без изменений.
        """
        return get_last_messages(limit)

    # ------------------------------------------------------------------
    # Семантический слой (ChromaDB) — см. отклонение от контракта выше
    # ------------------------------------------------------------------

    def index_semantic(self, text: str, role: str = "observation") -> None:
        """
        Точная замена app.py:add_to_chroma(text, role).

        Форматирование text (например, префикс "Эшли: "/"Дип: ") остаётся
        ответственностью вызывающего кода — Repository не решает, как
        должен выглядеть текст, только куда его положить.

        Ошибки глушатся (print, без raise) — как и в сегодняшнем
        add_to_chroma(). Это сохранение существующей асимметрии
        (запись в SQL прозрачно падает наружу, запись в Chroma — нет),
        не унификация.
        """
        try:
            self._chroma.add(
                documents=[text],
                metadatas=[{
                    "role": role,
                    "timestamp": dt.datetime.now().isoformat(),
                }],
                ids=[str(uuid.uuid4())],
            )
        except Exception as e:
            print(f"[CHROMADB] Ошибка сохранения: {e}")

    def semantic_recall(self, query: str, n: int = 3) -> str:
        """
        Точная замена app.py:query_chroma(query_text, n_results).

        Возвращает str (документы, склеенные через "\\n"), либо "" при
        отсутствии результатов или ошибке — ровно как сегодняшний
        query_chroma(). Сегодня эта функциональность нигде не вызывается
        в app.py (dead code) — Repository не меняет этот факт, только
        делает возможность доступной через явный API.
        """
        try:
            results = self._chroma.query(query_texts=[query], n_results=n)
            if results and results.get("documents") and results["documents"][0]:
                return "\n".join(results["documents"][0])
        except Exception as e:
            print(f"[CHROMADB] Ошибка поиска: {e}")
        return ""