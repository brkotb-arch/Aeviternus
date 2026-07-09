# Aeviternus Architecture Showcase

A technical overview of the Aeviternus persistent AI runtime — intended for engineers, researchers, and technical reviewers evaluating the project's architecture and engineering approach.

---

## What Aeviternus Is

Aeviternus is a **persistent runtime system** built around language models. It is not a chatbot wrapper.

The project explores **experimental AI infrastructure** where memory, identity, cognition, and autonomous processes exist as architectural layers rather than session-scoped instructions. The language model serves as a reasoning component inside a continuously operating runtime.

Key framing:

- **Persistent runtime system** — processes run beyond individual conversations
- **Adaptive interaction layer** — responses shaped by memory, identity, and state
- **Identity-oriented architecture** — behavioral continuity as a first-class component
- **Experimental AI infrastructure** — research-grade engineering, not a product demo

---

## Runtime Architecture

Aeviternus is organized around five core architectural concepts:

### Runtime Core

The execution environment that maintains the system between interactions.

- Lifecycle management via `connect.py`
- Request routing through Flask (`app.py`)
- Background thread coordination
- Graceful shutdown and state monitoring

### Identity Core

A persistent layer for behavioral continuity (`core/identity_layer.py`).

- Communication patterns and principles
- Priority and constraint definitions
- Mood-driven identity updates
- Architectural component, not a static system prompt

### Memory Fabric

Hybrid memory architecture combining structured and semantic storage.

- **SQLite** — conversations, facts, observations, events, mood history
- **ChromaDB** — semantic retrieval, contextual recall, vector associations
- **Memory router** (`core/memory_router.py`) — event classification and storage routing

### Cognitive Pipeline

The processing layer that transforms input into system behavior (`core/cognitive_engine.py` and related modules).

```
Input
 ↓
Context Formation
 ↓
Memory Activation
 ↓
Identity Alignment
 ↓
Reasoning (LLM)
 ↓
Response Generation
 ↓
Memory Update
```

Supporting modules: mood engine, thought router, silence detector, vision/OCR.

### Autonomous Cycles

Background processes that operate independently of user input:

| Cycle | Module | Purpose |
|-------|--------|---------|
| Think Cycle | `core/think_loop.py` | Internal reasoning and thought generation |
| Discovery Cycle | `app.py` (background thread) | Exploration and observation logging |
| Initiative Cycle | `initiative_rules.py` | Proactive outreach based on rules |

These cycles allow the runtime to maintain activity beyond direct user interaction.

---

## System Layers

```
┌─────────────────────────────────────┐
│         Interface Layer             │
│   Web UI · Telegram · Voice input   │
└─────────────────┬───────────────────┘
                  │
┌─────────────────v───────────────────┐
│          Runtime Layer              │
│   Runtime Core · Event Bus · State  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────v───────────────────┐
│         Cognitive Layer             │
│  Cognitive Pipeline · Identity Core │
│  Mood Engine · Thought Router       │
└─────────────────┬───────────────────┘
                  │
┌─────────────────v───────────────────┐
│          Memory Layer               │
│  Memory Fabric · Memory Router      │
│  ChromaDB retrieval · SQLite store  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────v───────────────────┐
│           Data Layer                │
│   SQLite (deep.db) · ChromaDB       │
│   File storage · Runtime logs       │
└─────────────────────────────────────┘
```

---

## Unique Engineering Decisions

### Local runtime architecture

Aeviternus runs as a self-contained Python process on local or VPS infrastructure. The runtime supervisor (`connect.py`) manages Flask, background cycles, and monitoring in a single deployment unit — no microservice overhead for the core loop.

### Persistent memory approach

Memory is not ephemeral context. Conversations, facts, and observations are stored in SQLite with semantic indexing in ChromaDB. The Memory Fabric survives session boundaries and informs future interactions through retrieval-augmented context formation.

### State-driven identity system

Identity is maintained as runtime state, updated through mood events and interaction history. The Identity Core influences response generation through the Cognitive Pipeline rather than relying solely on prompt engineering.

### Modular cognitive components

Cognitive functions are separated into focused modules under `core/`:

- `cognitive_engine.py` — pipeline orchestration
- `identity_layer.py` — identity state
- `mood_engine.py` — valence/arousal/clarity tracking
- `memory_router.py` — event classification and routing
- `think_loop.py` — autonomous thought generation
- `event_bus.py` — inter-module communication

Each module has a defined responsibility within the architecture.

### Runtime-defined autonomy

Autonomous Cycles operate as independent background processes inside the Aeviternus runtime.

Their behavior is determined by internal system logic, runtime state, configured rules (`initiative_rules.py`), and subsystem interactions rather than direct user requests.

The autonomy exists at the architectural level: the system can perform background operations, maintain internal state, process observations, and execute defined workflows independently while remaining inside the boundaries of its implemented runtime design.

---

## Beyond a Chatbot

| Typical chatbot | Aeviternus |
|-----------------|------------|
| Session-scoped context | Persistent Memory Fabric across sessions |
| Static system prompt | Identity Core with state-driven updates |
| Request-response only | Autonomous Cycles running in background |
| Single interface | Multi-interface (Web, Telegram, voice) |
| No internal state | Runtime state, mood history, event bus |
| Stateless deployment | Continuous runtime process |

Aeviternus treats the language model as one component inside a larger system. The architecture provides the structure that a long-lived AI runtime requires: memory, identity, cognition, and autonomous execution.

---

## Visual Interface

The web interface includes a **Reactive Avatar Layer** — an inline SVG face controlled by mood state through procedural DOM animation. See [Avatar Documentation](AVATAR.md) for technical details.

The interface also provides:

- Three CSS themes (purple, red, dark) with persistent selection
- Mood bar with six expression states
- Thoughts panel for autonomous cycle output
- Markdown-rendered responses with syntax highlighting

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.11+, Flask |
| Structured memory | SQLite |
| Semantic memory | ChromaDB |
| LLM | OpenAI-compatible API (DeepSeek) |
| Response formatting | markdown2 |
| Voice (optional) | Vosk, torch, sounddevice |
| CI | GitHub Actions |
| Frontend | Inline SVG, vanilla JavaScript, CSS |

---

## Documentation Index

| Document | Focus |
|----------|-------|
| [Architecture](ARCHITECTURE.md) | Full system architecture |
| [Runtime Model](RUNTIME.md) | Execution model and lifecycle |
| [Memory Architecture](MEMORY.md) | Memory Fabric design |
| [Identity System](IDENTITY.md) | Identity Core |
| [Cognitive Architecture](COGNITION.md) | Cognitive Pipeline |
| [Autonomous Cycles](LOOPS.md) | Background processes |
| [Avatar System](AVATAR.md) | SVG visual interface |
| [Deployment](DEPLOYMENT.md) | Local deployment guide |
| [Roadmap](ROADMAP.md) | Development direction |

---

## Project Status

Aeviternus is active experimental research software. Current stage: **Advanced Experimental AI Runtime Architecture**.

See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for completed capabilities, in-progress work, and known limitations.
