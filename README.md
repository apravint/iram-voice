# 🎙️ IRAM Voice: Open-Source VoiceStudio & MCP Server

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20PipeWire%20%7C%20Wayland-purple.svg)]()
[![Protocol](https://img.shields.io/badge/MCP-2024--11--05-brightgreen.svg)](https://modelcontextprotocol.io/)

**IRAM Voice** is an open-source voice design, video dubbing, and neural speech synthesis suite for Linux desktops. It bundles a native **Model Context Protocol (MCP)** server so AI coding agents can speak aloud and review code verbally through PipeWire.

> [!NOTE]
> The default engine uses `edge-tts`, which sends text to Microsoft's online service. The default `clone` and `design` commands only adjust EQ/pitch/rate parameters and timbral filters on stock voices; they do not reproduce the speaker. For true neural voice cloning, connect to a VoiceStudio backend.

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
   Neural Speech       Sample Storage &        Prompt-to-Preset        Video Dialogue &     Stdio MCP Server for
   via PipeWire        Acoustic EQ Matching    Personality Heuristics  Auto Sidechain Duck  Antigravity / Agents
```

---

## 🌟 Key Features

1. **Speech Synthesis**:
   - High-fidelity neural voice synthesis via PipeWire.
   - Select between `edge` (default, online Microsoft service), `voicestudio` (self-hosted backend), or `auto` fallback mode.
2. **Preset Voice Profiling & Design**:
   - `clone`: Stores a reference sample and applies EQ and harmonic filtering (does not reproduce speaker without VoiceStudio).
   - `design`: Heuristic voice persona generation adjusting pitch, rate, and base model presets from adjectives.
3. **Model Context Protocol (MCP) Server**:
   - Standard JSON-RPC stdio transport. Exposes `generate_speech`, `clone_voice`, `design_voice`, and `list_voices` directly to Claude Desktop, Google Antigravity, and OpenClaw.
4. **Video Dubbing with Auto-Ducking**:
   - Dips original background video audio by -14dB and mixes synchronized synthesized speech tracks into a master MP4.
5. **Bilingual & Multi-Language**:
   - Pre-loaded with English AI Copilot (`jarvis`), Conversationalist (`samantha`), Cinema Narrator (`cinema-narrator`), and Native Tamil voices (`tamil-tech` / Kavitha, `tamil-male` / Valluvan).

---

## 🔊 VoiceStudio Backend

For real voice cloning and self-hosted synthesis, connect IRAM Voice to a separately running VoiceStudio server.

### Running VoiceStudio
Run VoiceStudio separately on a computer or server:
- **Linux desktop**: Official desktop builds are x64.
- **ARM64 / Servers**: ARM64 Docker images require an NVIDIA GPU.
- **Android phones**: Use VoiceStudio's own APK, which is a separate Android application.

### Configuration
Configure the connection using environment variables:
- `VOICESTUDIO_URL`: Address of the VoiceStudio server (default: `http://localhost:3900`).
- `VOICESTUDIO_API_KEY`: Optional API key, sent as a `Bearer` token and never logged. Use HTTPS or a private network such as Tailscale for remote servers, because plain HTTP exposes the key and your text.
- `IRAM_VOICE_ENGINE`: Set default engine (`edge`, `voicestudio`, or `auto`).

### Example Commands
```bash
# List available voices on VoiceStudio
iram-voice vs-voices

# Synthesize speech using VoiceStudio engine
iram-voice speak "Synthesizing with VoiceStudio" --engine voicestudio

# Synthesize using a specific VoiceStudio cloned voice profile
iram-voice speak "Speaking with my cloned voice profile" --engine voicestudio --vs-voice "CustomClone"

# Auto engine (tries VoiceStudio first, falls back to edge on failure)
iram-voice speak "Resilient synthesis with auto fallback" --engine auto
```

### License & Ethics Notice
- VoiceStudio is licensed under **AGPL-3.0** and is installed separately; no VoiceStudio code is included in this repository.
- **Consent Notice**: Only obtain real cloning with consent of the speaker.

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
# Speak text through PipeWire (default edge-tts)
iram-voice speak "System kernel upgraded to Linux 6.17. Audio bus online."

# Speak with Deep Cinema Narrator
iram-voice speak "In a world ruled by autonomous swarms, one desktop stands sovereign." --voice cinema-narrator

# Speak in Tamil
iram-voice speak "வணக்கம், ஐராம் ஓஎஸ் குரல் ஸ்டுடியோ தயார் நிலையில் உள்ளது." --voice tamil-tech

# Store a reference sample and apply EQ profile
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
