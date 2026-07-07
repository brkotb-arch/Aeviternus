# Aeviternus

Documen# Aeviternus Autonomous Loops


## Overview

Aeviternus contains background processes that allow the runtime to perform actions outside direct user interaction.


These processes create continuous system activity.


---

# Current Loops


## think_loop


Purpose:

Internal processing and maintenance.


Responsibilities:

- analyze recent events
- update internal state
- perform self-checks


---

## curiosity_loop


Purpose:

Information discovery.


Responsibilities:

- search external sources
- collect interesting information
- create discoveries


Future:

- autonomous research
- knowledge expansion


---

## initiative_loop


Purpose:

Controlled proactive interaction.


Responsibilities:

- generate suggestions
- notify important events
- provide system updates


---

# Loop Architecture

              Runtime
                 |
          Event Scheduler
                 |
    -----------------------------
    |             |             |
 Think Loop   Curiosity Loop  Initiative Loop



---

# Current Limitations


## Shared LLM Resource

Multiple loops can compete for model access.


Solution:

Arbitration Queue.


---

## Missing Priority System

Not every action has equal importance.


Future:

Priority-based execution.


---

## Resource Management

Future improvements:

- CPU limits
- memory limits
- execution timeout
- failure recovery