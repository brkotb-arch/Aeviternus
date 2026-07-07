# Aeviternus Memory Architecture

## Philosophy

Memory is not simple storage.

The goal is to create a system where information has meaning, priority and lifecycle.

---

# Current Architecture

## Short-Term Memory

Contains:

- recent messages
- current conversation context


## Long-Term Memory

Implemented using:

- SQLite
- ChromaDB


---

# SQLite Memory

Stores:

- facts
- observations
- conversations
- moods
- events


---

# Vector Memory

ChromaDB provides:

- semantic search
- contextual retrieval
- historical recall


---

# Planned Improvements

## Memory Router

A classification layer deciding:

- what becomes a fact
- what becomes context
- what should be ignored


## Memory Importance

Each memory should have:

- importance score
- timestamp
- confidence
- category


## Memory Consolidation

Future system:

- daily summaries
- conflict detection
- outdated information cleanup