<div align="center">

# Aeviternus

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Architecture](https://img.shields.io/badge/Architecture-Cognitive_Runtime-purple)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active_Development-orange)
![Repository Layer](https://img.shields.io/badge/Repository_Layer-Phase_1_Complete-gold)
![Tests](https://github.com/brkotb-arch/Aeviternus/actions/workflows/python.yml/badge.svg)

### A Cognitive Runtime for Persistent AI Systems

**Memory · Identity · Cognition · Autonomy · Repository Layer**

---

**Experimental AI Systems Research Project**

Aeviternus explores the architecture of long-lived AI systems:
systems capable of maintaining memory, behavioral continuity, internal state and autonomous processes beyond individual conversations.

---

Designed and developed by Ashley (NOIRMURR)

</div>

---

> **Status:** Active Development  
> **Language:** Python 3.11+  
> **Architecture:** Runtime-based AI System evolving toward Modular Kernel  
> **Current Version:** v0.2.4  
> **Latest Feature:** Repository Layer — Phase 1: ConversationRepository

---

# Why Aeviternus?

Unlike conventional chatbots that lose context when a conversation ends, Aeviternus explores a persistent runtime architecture where memory, identity, cognition and autonomous background processes remain active over time.

The language model is only one component of the system.

The surrounding runtime provides continuity, behavioral state, memory routing, autonomous thinking cycles and long-term evolution.

Current implementation includes:

- Persistent Memory Fabric (SQLite + ChromaDB)
- Identity Core
- Cognitive Pipeline
- Autonomous Cycles
- Runtime State Management
- Reactive SVG Avatar
- Repository Layer (Phase 1: ConversationRepository)
- Telegram Integration
- Voice Input (optional)
- Research-oriented modular architecture

---

# Vision

Current AI systems are highly capable, but most of them exist only as temporary interactions.

A conversation starts.

Context appears.

The session ends.

Aeviternus explores a different direction:

> AI as a persistent computational process.

A system where memory, identity, cognition and autonomy exist as architectural layers rather than temporary instructions.

The project investigates how software architecture can enable AI systems to maintain continuity over time:

- remembering previous interactions
- preserving behavioral patterns
- adapting through experience
- operating through autonomous processes
- developing a persistent internal state

The goal is not to replace language models.

The goal is to explore the architecture that allows them to become part of a larger, continuously operating system.

---

# What is Aeviternus?

Aeviternus is not a traditional chatbot.

It is an experimental cognitive runtime built around the idea that intelligence requires more than generation.

A long-lived AI system requires:

- memory
- identity
- state
- reflection
- autonomous execution
- environmental interaction

The language model is treated as a reasoning component inside this architecture.

---

# Core Architecture

```
User
 ↓
Interface Layer
 ↓
Runtime Core
 ↓
Memory Fabric
Identity Core
Cognitive Pipeline
 ↓
Autonomous Cycles
 ↓
Reflection System
 ↓
LLM Provider
```

---

# Architectural Concepts

## Runtime Core

The execution environment responsible for maintaining the system.

Responsibilities:

- lifecycle management
- state coordination
- subsystem communication
- process execution

## Identity Core

A persistent layer responsible for behavioral continuity.

It contains:

- communication patterns
- principles
- priorities
- constraints
- adaptive behavioral information

Identity is treated as an architectural component rather than a simple system prompt.

## Memory Fabric

A hybrid memory architecture designed to preserve meaningful information.

### Structured Memory

Powered by SQLite.

Stores:

- conversations
- facts
- observations
- events
- runtime information

### Semantic Memory

Powered by vector storage.

Provides:

- semantic retrieval
- contextual recall
- historical associations

Future development:

- memory importance scoring
- consolidation
- conflict resolution
- lifecycle management

## Cognitive Pipeline

The cognitive layer transforms input into system behavior.

Pipeline:

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
Response Generation
 ↓
Evaluation
 ↓
Memory Update
```

## Autonomous Cycles

Aeviternus contains background processes designed to maintain continuous activity.

Current cycles:

- Think Cycle
- Discovery Cycle
- Initiative Cycle

These processes allow the system to perform operations beyond direct user interaction.

## Reflection System

Future architecture for:

- analyzing previous interactions
- evaluating decisions
- identifying improvements
- refining future behavior

---

## Repository Layer *(New in v0.2.4)*

A new architectural boundary introduced to formalize data access between `app.py` and persistence backends.

**Phase 1: ConversationRepository** is now live.

**Design Principles:**
- Adapter pattern over existing `db.py`/`chroma_singleton.py`
- Stateless by design
- No business logic — only persistence translation
- No EventBus subscription
- Zero behavioral changes

**Upcoming Phases:**
1. ✅ ConversationRepository
2. ⬜ MoodHistoryRepository
3. ⬜ DiscoveryRepository
4. ⬜ FactRepository
5. ⬜ ThoughtRepository
6. ⬜ ContextRepository
7. ⬜ MemoryRepository
8. ⬜ IdentityRepository

# Current Capabilities

---

Implemented:

| Component | Status |
|------------|--------|
| Runtime Core | ✅ |
| Memory Fabric | ✅ |
| Identity Core | ✅ |
| Cognitive Pipeline | ✅ |
| Autonomous Cycles | ✅ |
| Reactive SVG Avatar | ✅ |
| Repository Layer (Phase 1) | ✅ |
| Telegram Bridge | ✅ |
| Semantic Memory | ✅ |
| Voice Input | Optional |
| Reflection System | In Progress |
| Local LLM Runtime | Planned |

---

# Technology Stack

## Backend

- Python 3.11+
- Flask

## Data

- SQLite
- ChromaDB

## AI Systems

- OpenAI-compatible API (DeepSeek)
- markdown2 (response formatting)
- ChromaDB retrieval (Memory Fabric)
- Autonomous Cycles (Think, Discovery, Initiative)
- Cognitive Pipeline

## Optional

- Vosk + torch + sounddevice (voice input)

## Infrastructure

- GitHub Actions (CI)
- Linux (deployment target)

---

# Runtime Components

| Layer | Description |
|---------|-------------|
| Runtime Core | Lifecycle, orchestration and process management |
| Identity Core | Persistent behavioral continuity |
| Memory Fabric | Structured and semantic memory |
| Cognitive Pipeline | Reasoning and response generation |
| Autonomous Cycles | Independent background execution |
| Reactive Avatar | Runtime visual representation |
| Repository Layer | Persistence abstraction and data access |

---

# Research Directions

Aeviternus explores:

- persistent AI architectures
- identity continuity
- memory-driven systems
- autonomous runtime design
- local AI infrastructure
- long-term adaptive behavior
- architectural patterns for persistent AI

---

# Engineering Principles

The project follows:

- Runtime before interface.
- Memory before conversation.
- Identity before personality simulation.
- Architecture before features.
- Systems before isolated components.
- Continuous evolution instead of isolated sessions.
- Local-first whenever practical.
- Transparent engineering over hidden complexity.
- Human-supervised autonomy.
- Repository-driven persistence.

---

# Project Structure

```
Aeviternus/
├── app.py                    # Main Flask application
├── connect.py                # Runtime entry point
├── db.py                     # Database access layer
├── storage.py                # Legacy storage (deprecated)
├── DI_CORE_plugin.py         # Search plugin
├── initiative_rules.py       # Initiative cycle rules
├── requirements.txt          # Python dependencies
├── core/                     # Core modules
│   ├── cognitive_engine.py   # Cognitive processing
│   ├── event_bus.py          # Event system
│   ├── identity_layer.py     # Identity management
│   ├── mood_engine.py        # Mood system
│   ├── silence_detector.py   # Silence detection
│   ├── think_loop.py         # Think cycle
│   ├── thought_router.py     # Thought routing
│   ├── memory_router.py      # Memory routing
│   ├── chroma_singleton.py   # ChromaDB singleton
│   ├── vision.py             # Vision/OCR module
│   ├── state_manager.py      # Runtime state management
│   ├── cognitive_context.py  # Cognitive context formation
│   └── repositories/         # Repository Layer
│       ├── __init__.py       # Package marker
│       └── conversation_repository.py  # Phase 1 complete
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # Architecture overview
│   ├── COGNITION.md          # Cognitive pipeline
│   ├── DESIGN.md             # Design principles
│   ├── DEPLOYMENT.md         # Deployment guide
│   ├── EVOLUTION.md          # Project evolution
│   ├── FAQ.md                # Frequently asked questions
│   ├── IDENTITY.md           # Identity system
│   ├── LOOPS.md              # Autonomous cycles
│   ├── MEMORY.md             # Memory architecture
│   ├── OBSERVABILITY.md      # Observability system
│   ├── RESEARCH.md           # Research areas
│   ├── ROADMAP.md            # Project roadmap
│   ├── RUNTIME.md            # Runtime model
│   ├── CONTRIBUTING.md       # Contributing guide
│   ├── AVATAR.md             # Reactive SVG Avatar architecture
│   ├── SHOWCASE.md           # Architecture showcase
│   └── API.md                # API documentation
├── tests/                    # Test suite
├── static/                   # Static assets
├── templates/                # HTML templates
├── data/                     # Runtime data (gitignored)
├── logs/                     # Application logs (gitignored)
├── model/                    # Vosk model (gitignored)
└── archive/                  # Archived modules
```

---

# Documentation

Complete documentation is available in the `/docs` directory:

- [Architecture](docs/ARCHITECTURE.md) - System architecture overview
- [Runtime Model](docs/RUNTIME.md) - Runtime execution model
- [Memory Architecture](docs/MEMORY.md) - Memory system design
- [Identity System](docs/IDENTITY.md) - Identity layer documentation
- [Cognitive Architecture](docs/COGNITION.md) - Cognitive pipeline
- [Autonomous Cycles](docs/LOOPS.md) - Background processes
- [Security Model](SECURITY.md) - Security policy
- [Observability](docs/OBSERVABILITY.md) - Monitoring and logging
- [Roadmap](docs/ROADMAP.md) - Development roadmap
- [Design Principles](docs/DESIGN.md) - Engineering principles
- [Philosophy](docs/PHILOSOPHY.md) - Research philosophy
- [Origin](docs/ORIGIN.md) - Project history
- [Research](docs/RESEARCH.md) - Research areas
- [FAQ](docs/FAQ.md) - Frequently asked questions
- [API](docs/API.md) - API documentation
- [Deployment](docs/DEPLOYMENT.md) - Deployment guide
- [Contributing](docs/CONTRIBUTING.md) - Contribution guidelines
- [Avatar System](docs/AVATAR.md) - Reactive SVG avatar architecture, expression mapping and procedural animation
- [Architecture Showcase](docs/SHOWCASE.md) - Technical overview of Aeviternus architecture for engineers and reviewers

---

# Engineering Goals

Current focus of development:

- Runtime modularization
- Memory consolidation
- Better autonomous reasoning
- Local-first deployment
- Multi-provider LLM abstraction
- Long-term identity persistence
- Runtime observability
- **Repository Layer** — Complete all 8 phases (currently: Phase 1 ✅)

---

# Future Vision

Aeviternus aims to become a modular, extensible runtime kernel for persistent AI systems.

Long-term goals include:

- **Modular Kernel**: Extract core runtime into a reusable kernel
- **Runtime Plugins**: Enable third-party extensions
- **Identity Evolution**: Track and adapt identity over time
- **Memory Consolidation**: Automatic memory importance scoring and cleanup
- **Local-first Runtime**: Full local inference capability
- **Multi-Agent Collaboration**: Support for multiple autonomous agents
- **Distributed Memory Fabric**: Shared memory across instances
- **Reflection System**: Self-analysis and behavioral refinement

The project explores the possibility that persistent intelligence may require not only models, but architectures capable of memory, continuity and growth.

---

# Author

Ashley (NOIRMURR)

GitHub:
https://github.com/brkotb-arch

---

> *Aeviternus is an ongoing research project exploring what software architecture may be required for persistent artificial intelligence.*

If this project interests you, feel free to open an Issue, start a Discussion or contribute ideas.
