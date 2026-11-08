# AGENTS.md - Developer & AI Agent Operations Manual for `iram-voice` 🤖

This document is the definitive operational guide for autonomous AI coding agents (Antigravity, Claude, Cursor, OpenAI Codex, OpenHands) operating within this repository.

---

## 🎯 1. System Overview & Core Philosophy

**🎙️ IRAM Voice: Open-Source VoiceStudio & MCP Server**
> IRAM Voice is a small Python CLI and Model Context Protocol (MCP) server for Linux desktops. It wraps edge-tts (or an optional self-hosted VoiceStudio backend) for speech synthesis, keeps a set of voice presets, and can mix a synthesized voice track into a video with ffmpeg. The MCP server lets AI agents trigger speech; playback uses the first available of pw-play, paplay, aplay or mpv. The default engine uses edge-tts, which sends text to Microsoft's online service. clone only stores a 16 kHz mono copy of your sample and, with the edge engine, applies a fixed EQ/compressor chain to the output; design only picks a stock voice with pitch/rate offsets from keywords. Neither reproduces a speaker. For true neural voice cloning, connect to a VoiceStudio backend. ┌────────────────────────────────────────────────────────┐

### Key Architectural Capabilities
- **Speech Synthesis**: 
- **Preset Voice Profiling & Design**: 
- `clone`: Converts the sample to 16 kHz mono WAV and registers a profile. The reference audio is only used for a fixed bass/treble/compressor filter on edge output; it is not sent to VoiceStudio and does not reproduce the speaker.
- `design`: Keyword matching on the description (e.g. deep/high, fast/slow, male/female, tamil) picks pitch, rate and a stock edge voice.
- **Model Context Protocol (MCP) Server**: 
- **Video Dubbing with Auto-Ducking**: 

---

## 🏗️ 2. Repository Structure & Directory Map

| Path | Role & Architectural Responsibility |
| :--- | :--- |
| `.github/` | Subsystem directory (.github) |
| `bin/` | Executable CLI scripts and dispatchers |
| `iram_voice/` | Main Python application package |
| `pyproject.toml` | Python package configuration, dependencies, and tool settings |
| `tests/` | Automated test suite (unit, integration, regression) |

---

## ⚙️ 3. Executable Verification Pipeline

Before marking any task complete, an AI agent **must** run the following verification steps sequentially:

### Tier 1: Syntax & Bytecode Compilation Check (< 2 seconds)
Ensures all modified Python files parse cleanly with zero syntax or indentation errors:
```bash
python3 -m py_compile $(find . -maxdepth 3 -name '*.py' -not -path '*/.*' -not -path '*/venv/*')
```

### Tier 2: Static Analysis & Linting
```bash
ruff check . || flake8 . || python3 -m py_compile **/*.py
```

### Tier 3: Automated Test Suite (Fast Offline / Mocked)
Verifies functional regressions across all unit tests:
```bash
pytest -v
```

### Tier 4: Smoke Test / CLI Verification
Run a non-destructive dry-run or help check to confirm executable health:
```bash
iram-voice vs-voices
iram-voice speak "Synthesizing with VoiceStudio" --engine voicestudio
```

---

## 🛡️ 4. Architectural Invariants & Non-Negotiable Rules

### Strict Invariants ("Never Do" List):
1. **Never Introduce Silent Mock Fallbacks:** If an external LLM, API, or system binary fails, raise an explicit, descriptive exception. Never return mock strings that mask runtime failures.
2. **Strict Type Annotations:** All new function signatures must include Python type annotations (`typing`, `pydantic`, or native dataclasses).
3. **Zero Hardcoded Secrets or Paths:** Never embed API keys, bearer tokens, or absolute paths (e.g., `/home/apravint`). Use `os.environ` or XDG specification paths.

### Security & Environment Variables:
- All API keys and secrets must be loaded strictly from environment variables.
  - `VOICESTUDIO_API_KEY`
- Never commit `.env`, `.pem`, token files, or private credentials.

---

## 🤖 5. Autonomous Agent Operational Protocol

When dispatched to resolve an issue, implement a feature, or refactor code in this repo:

1. **Phase 1 — Explore & Plan:**
   - Read this `AGENTS.md` and relevant source files.
   - Check existing tests to establish the baseline.
2. **Phase 2 — Act (Surgical Implementation):**
   - Implement changes with minimal blast radius.
   - Adhere to the established code style and existing conventions.
3. **Phase 3 — Verify:**
   - Run the Tier 1, 2, and 3 verification commands listed above.
   - Ensure all existing and new tests pass cleanly.
4. **Phase 4 — Reflect:**
   - Review `git diff` to confirm zero unintended whitespace or collateral changes.
   - Confirm no untracked scratch files remain.

---
*Maintained by Ayyappa Pravin • Engineered for Antigravity, Claude, Cursor & Modern Autonomous AI Agents.*
