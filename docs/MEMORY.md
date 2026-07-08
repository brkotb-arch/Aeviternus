# Aeviternus Memory Architecture

## Philosophy

Memory is not just storage.

The goal is to create a system where information has meaning, priority, relevance, and lifecycle.

Aeviternus treats memory as an active component of the runtime architecture rather than a passive data repository.

---

# Memory Fabric

```
Memory Fabric
├── Structured Memory
├── Semantic Memory
├── Runtime Memory
├── Context Memory
└── Reflection Memory
```

---

## Structured Memory

Implemented using SQLite.

Stores:

- facts
- observations
- conversations
- behavioral states
- events
- system metadata

---

## Semantic Memory

Implemented using ChromaDB.

Provides:

- semantic search
- contextual retrieval
- historical recall
- similarity-based information discovery

---

## Runtime Memory

Contains:

- recent messages
- current conversation context
- active interaction state
- runtime state

---

## Context Memory

Temporary context for:

- current session
- active processing
- short-term information
- working memory

---

## Reflection Memory

Future component for:

- self-analysis
- decision evaluation
- behavior refinement
- learning from experience
