# Aeviternus Runtime

## Purpose

The Runtime is the execution environment responsible for keeping Aeviternus continuously active.

Unlike a traditional chatbot that exists only during user interaction, Aeviternus is designed as a persistent process with internal state, background activity, and autonomous execution.

---

# Runtime State

The runtime maintains a comprehensive state containing:

## Active Context

- Current conversation context
- Recent messages
- Active interaction state
- Session information

## Memory State

- Memory system status
- Active memory operations
- Memory consolidation state
- Retrieval cache

## Identity State

- Current identity parameters
- Behavioral mode
- Mood state
- Identity evolution tracking

## Environment State

- System resources
- External connections
- Service availability
- Configuration state

## Active Processes

- Background cycles status
- Task queue state
- Process health
- Execution metrics

---

# Runtime Responsibilities

The runtime manages:

- incoming requests
- background loops
- memory operations
- system state
- model communication
- component coordination

---

# Execution Flow

```mermaid
flowchart TD

    Input[User Input]
    Validation[Request Validation]
    Context[Context Retrieval]
    Memory[Memory Search]
    Identity[Identity Layer]
    LLM[LLM Generation]
    Update[Memory Update]
    Response[Response]

    Input --> Validation
    Validation --> Context
    Context --> Memory
    Memory --> Identity
    Identity --> LLM
    LLM --> Update
    Update --> Response
```

---

# Current Runtime Components

## `connect.py`

Main runtime entry point.

Responsibilities:

- startup sequence
- process initialization
- service supervision
- runtime configuration loading

---

## `app.py`

Main web server component.

Responsibilities:

- HTTP routes
- user communication
- API handling
- request processing

---

## Background Services

Autonomous processes running independently from direct user interaction:

- `think_loop`
- `curiosity_loop`
- `initiative_loop`

---

# Future Runtime Kernel

Planned improvements:

- centralized task scheduler
- LLM request queue
- priority management system
- resource management
- failure recovery
- runtime monitoring
