# Aeviternus FAQ

## Is Aeviternus an AI model?

No.

It is an AI Runtime.

---

## Does it replace LLMs?

No.

LLMs are components inside the Runtime.

---

## Is it autonomous?

Partially.

Human supervision remains part of the architecture.

---

## Can it run locally?

This is one of the long-term goals.

---

## Is this a chatbot?

No.

Aeviternus is designed as an AI runtime that combines language models with persistent memory, internal state management, identity processing, and Autonomous Cycles.

The goal is not only conversation, but the creation of a continuously evolving AI system.

---

## Does Aeviternus have its own model?

Currently:

Aeviternus uses external LLM providers as reasoning engines.

Future:

The architecture supports local inference through solutions such as Ollama and other self-hosted models.

---

## Why SQLite and ChromaDB?

SQLite stores structured information:

- facts
- events
- system state
- runtime data

ChromaDB provides semantic retrieval:

- contextual memories
- concepts
- previous interactions

Together they form a hybrid memory architecture.

---

## Why not use only a system prompt?

A system prompt alone does not provide:

- persistent memory
- internal state
- identity continuity
- memory management
- Autonomous Cycles

Aeviternus treats the LLM as one component inside a larger runtime architecture.

---

## Is Aeviternus production ready?

Current stage:

Advanced prototype.

Before production deployment, the system requires:

- comprehensive testing
- security hardening
- deployment improvements
- monitoring and observability

---

## What is the long-term goal of Aeviternus?

Aeviternus explores the architecture of persistent AI systems capable of maintaining continuity, adapting over time, and developing a consistent internal model of interaction.

The project focuses on building the foundations for a long-lived AI runtime rather than a traditional conversational assistant.
