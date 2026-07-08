# Aeviternus Architecture

## Overview

Aeviternus is a persistent AI runtime designed around long-term memory, autonomous processes, and adaptive identity.

The system is built as a continuously running environment where the language model acts as a reasoning engine connected to external memory, state management, and autonomous execution loops.

---

# High-Level Architecture

```
User
 ↓
Interface Layer (Web, Telegram)
 ↓
API
 ↓
Runtime Core
 ↓
Memory Fabric (SQLite, ChromaDB, State)
Identity Core
Cognitive Pipeline
Autonomous Cycles
 ↓
LLM Provider
```

---

# Architecture Flow

```
User
↓
Interface Layer
↓
Runtime Core
↓
Runtime State
↓
Memory Fabric
↓
Identity Core
↓
Cognitive Pipeline
↓
Autonomous Cycles
↓
LLM Provider
```

# Core Layers

## 1. Interface Layer

Responsible for communication channels.

Current interfaces:

- Web application
- Telegram integration
- Voice interface

Responsibilities:

- Receive input
- Validate requests
- Display responses
- Handle sessions


---

# 2. Runtime Core

The runtime coordinates all internal components.

Responsibilities:

- Request routing
- State management
- Memory access
- Background processes
- Error handling


---

# 3. Memory Fabric

Aeviternus uses hybrid memory architecture.

## SQLite

Stores structured information:

- conversations
- facts
- observations
- moods
- events
- system state


## ChromaDB

Stores semantic information:

- previous conversations
- concepts
- discoveries
- contextual memories


---

# 4. Cognitive Pipeline

Responsible for response generation logic.

Components:

- identity processing
- mood adaptation
- context preparation
- self-analysis


---

# 5. Autonomous Cycles

Background processes running independently:

- Think Cycle
- Discovery Cycle
- Initiative Cycle


These processes allow the system to operate beyond direct user requests.

---

# Future Architecture

Planned improvements:

- Arbitration Kernel
- LLM Queue
- Memory Router
- Local Ollama Runtime
- Advanced context compression
- Improved observability

See [ROADMAP.md](ROADMAP.md) for detailed version planning.
