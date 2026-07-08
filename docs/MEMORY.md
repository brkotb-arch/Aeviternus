# Aeviternus Memory Architecture

## Philosophy

Memory is not just storage.

The goal is to create a system where information has meaning, priority, relevance, and lifecycle.

Aeviternus treats memory as an active component of the runtime architecture rather than a passive data repository.

---

# Current Architecture

## Short-Term Memory

Contains:

- recent messages
- current conversation context
- active interaction state

---

## Long-Term Memory

Implemented using:

- SQLite
- ChromaDB

Long-term memory combines structured storage with semantic retrieval.

---

# SQLite Memory

SQLite stores structured information:

- facts
- observations
- conversations
- behavioral states
- events
- system metadata

---

# Vector Memory

ChromaDB provides semantic memory capabilities:

- semantic search
- contextual retrieval
- historical recall
- similarity-based information discovery

---

# Planned Improvements

## Memory Router

A classification layer responsible for deciding:

- what becomes a permanent fact
- what remains temporary context
- what should be ignored or discarded

---

## Memory Importance

Each memory entry should contain metadata such as:

- importance score
- timestamp
- confidence level
- category
- relevance

---

## Memory Consolidation

Future memory processing system:

- automated daily summaries
- conflict detection
- outdated information cleanup
- memory optimization
- knowledge organization
