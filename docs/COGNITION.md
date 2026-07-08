# Aeviternus Cognitive Architecture

## Overview

The Cognitive Pipeline is responsible for transforming raw user input into meaningful system behavior.

It connects:

- user interaction
- memory retrieval
- identity state
- emotional state
- reasoning processes
- response generation

The Cognitive Pipeline is not the language model itself.

The LLM is treated as a reasoning engine operating inside a larger runtime architecture.

---

# Cognitive Pipeline

```
Input
↓
Context Formation
↓
Memory Activation
↓
Identity Alignment
↓
Reasoning
↓
Evaluation
↓
Memory Update
```

---

# Cognitive Components

## Context Builder

Responsible for preparing relevant information before response generation.

Collects:

- recent conversation context
- relevant memories
- system state
- identity information

---

## Identity Core

Maintains behavioral consistency across interactions.

Responsible for:

- communication style
- priorities
- interaction patterns
- behavioral constraints

---

## Mood Engine

Manages dynamic runtime state affecting interaction behavior.

Current states:

- `NEUTRAL`
- `SASS_ON`
- `DARK`
- `SOFT`
- `FOCUS`
- `CHAOS`

Mood influences:

- response style
- tone
- interaction strategy

---

# Self Evaluation

After generating a response, the system can perform internal evaluation.

Evaluation criteria:

- relevance
- usefulness
- tone consistency
- behavioral consistency

The evaluation result can influence future interactions and runtime adjustments.

---

See [ROADMAP.md](ROADMAP.md) for future cognitive architecture improvements including Arbitration Layer, Reasoning Memory, and Reflection System.
