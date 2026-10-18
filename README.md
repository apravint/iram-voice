# 🎙️ IRAM Voice: Open-Source VoiceStudio & MCP Server

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20PipeWire%20%7C%20Wayland-purple.svg)]()
[![Protocol](https://img.shields.io/badge/MCP-2024--11--05-brightgreen.svg)](https://modelcontextprotocol.io/)

**IRAM Voice** is a fully-local, open-source voice cloning, prompt-based voice design, video dubbing, and neural speech synthesis suite for Linux desktops. Inspired by [debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio) and OmniVoice, it bundles a native **Model Context Protocol (MCP)** server so AI coding agents can speak aloud, clone voices, and review code verbally through PipeWire.

---

## 🏛️ Architecture

```
                          ┌────────────────────────────────────────────────────────┐
                          │               IRAM VOICE STUDIO ENGINE                 │
                          └──────────────────────────┬─────────────────────────────┘
                                                     │
         ┌───────────────────┬───────────────────────┼───────────────────────┬────────────────────┐
         ▼                   ▼                       ▼                       ▼                    ▼
   [iram-voice speak]  [iram-voice clone]      [iram-voice design]     [iram-voice dub]     [iram-voice mcp]
   Neural Speech       Zero-Shot Cloning from  Prompt-to-Voice         Video Dialogue &     Stdio MCP Server for
   via PipeWire        5-10s Reference Audio   Personality Engine      Auto Sidechain Duck  Antigravity / Agents
```

---

## 🌟 Key Features

1. **Zero-Shot Voice Cloning**:
   - Provide a short 5–10s reference audio sample (`.wav` / `.mp3`).
   - Normalizes audio to 16kHz mono and enrolls a persistent voice profile.
2. **Prompt-Based Voice Design**:
   - Describe a voice personality with natural language (e.g., *"deep resonant film director with calm pacing"* or *"warm British narrator"*).
   - Generates acoustic pitch, rate, and timbre parameters automatically.
3. **Model Context Protocol (MCP) Server**:
   - Standard JSON-RPC stdio transport. Exposes `generate_speech`, `clone_voice`, `design_voice`, and `list_voices` directly to Claude Desktop, Google Antigravity, and OpenClaw.
4. **Video Dubbing with Auto-Ducking**:
   - Dips original background video audio by -14dB and mixes synchronized synthesized speech tracks into a master MP4.
5. **Bilingual & Multi-Language**:
   - Pre-loaded with English AI Copilot (`jarvis`), Conversationalist (`samantha`), Cinema Narrator (`cinema-narrator`), and Native Tamil voices (`tamil-tech` / Kavitha, `tamil-male` / Valluvan).

---

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/apravint/iram-voice.git
cd iram-voice

# Make executable available in PATH
mkdir -p ~/.local/bin
ln -sf $(pwd)/bin/iram-voice ~/.local/bin/
```

### 2. Basic Usage

```bash
# Speak text through PipeWire
iram-voice speak "System kernel upgraded to Linux 6.17. Audio bus online."

# Speak with Deep Cinema Narrator
iram-voice speak "In a world ruled by autonomous swarms, one desktop stands sovereign." --voice cinema-narrator

# Speak in Tamil
iram-voice speak "வணக்கம், ஐராம் ஓஎஸ் குரல் ஸ்டுடியோ தயார் நிலையில் உள்ளது." --voice tamil-tech

# Clone a voice from audio
iram-voice clone /path/to/sample.wav --name "MyVoice" --gender male

# Design a synthetic persona
iram-voice design "deep calm cyberpunk detective" --name "K-2049"

# Dub a video
iram-voice dub input.mp4 --text "Here is our newly trained agent model." --voice cinema-narrator --out dubbed.mp4

# Run MCP Server for AI Agents
iram-voice mcp
```

---

## 🤖 MCP Server Configuration

To connect `iram-voice` to **Claude Desktop**, **Antigravity CLI**, or **OpenClaw**, add to your MCP settings:

```json
{
  "mcpServers": {
    "iram-voice": {
      "command": "iram-voice",
      "args": ["mcp"]
    }
  }
}
```

---

## 📜 License
MIT License. Created by [Pravin](https://github.com/apravint) for IRAM OS.
