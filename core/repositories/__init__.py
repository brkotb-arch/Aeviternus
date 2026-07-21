"""
Repository Layer (Aeviternus).

Аддитивный слой между app.py и физическими хранилищами (db.py, chroma_singleton.py).
Не содержит состояния, не содержит бизнес-логики, не подписывается на EventBus.

См. ARCHITECTURE_DICTIONARY.md, OWNERSHIP_DICTIONARY.md,
REPOSITORY_DESIGN.md, REPOSITORY_CONTRACTS.md, REPOSITORY_IMPLEMENTATION_PLAN.md.
"""