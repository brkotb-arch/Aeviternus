# Changelog

All notable changes to Aeviternus are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.1] - 2026-07

### Added

- LLM retry mechanism with exponential backoff (max 3 attempts)
- Detailed error handling for LLM API calls:
  - Timeout errors
  - Authentication errors
  - Connection errors
  - Rate limit errors
  - API errors
  - Empty response detection
- API key validation at startup with clear error messages
- Timeout parameter (30s) to all LLM API calls
- Graceful error handling in Background Cycles (Think, Discovery, Initiative)
- Improved frontend error messages with server status indicators

### Changed

- Increased Think Cycle max_tokens from 800 to 1000 for complete thought generation
- Replaced direct `client.chat.completions.create` calls with `call_llm_with_retry` helper
- Updated all LLM calls to use retry mechanism:
  - Cognitive Pipeline
  - Think Cycle
  - Discovery Cycle
  - Initiative Cycle
  - File upload analysis
  - Voice recognition
  - Post generation
  - Self-review
- Fixed SQLite row_factory configuration for proper Row/dict conversion
- Fixed requests import alias (requests → req) in Curiosity Cycle
- Improved frontend error handling to display specific error messages

### Fixed

- Connection errors in LLM API calls
- Think Cycle interruptions due to connection failures
- Dictionary update sequence error in DB layer
- Missing requests import causing Curiosity Cycle failures
- Generic "Ошибка соединения..." message replaced with specific error details

### Security

- Added fail-fast API key validation to prevent runtime without credentials

---

## [0.2.0] - 2026-07

### Added

- Complete project documentation
- Architecture documentation
- Identity layer documentation
- Cognitive architecture documentation
- Runtime documentation
- Roadmap
- Security model
- Archive directory for legacy modules

### Changed

- Unified terminology across documentation
- Memory System → Memory Fabric
- Cognitive Layer → Cognitive Pipeline
- Autonomous Processes → Autonomous Cycles
- Updated cycle naming (Think Cycle, Discovery Cycle, Initiative Cycle)

### Removed

- Duplicate documentation files (SECURITY.md, SECURITY_POLICY.md)
- Root-level CONTRIBUTING.md and ROADMAP.md (consolidated into docs/)
- Legacy modules (deep_core.py)

### Security

- Added supervisor.log to .gitignore

---

## [0.1.0] - 2026-07

### Added

- Runtime Core
- Memory System (SQLite + ChromaDB)
- Identity Layer
- Background Processing
- Flask web interface
- Telegram integration
- GitHub Infrastructure
- CI
- MIT License
- Project Branding