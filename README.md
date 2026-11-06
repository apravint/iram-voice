# 🎙️ IRAM Voice: Open-Source VoiceStudio & MCP Server

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20PipeWire-purple.svg)]()
[![Protocol](https://img.shields.io/badge/MCP-2024--11--05-brightgreen.svg)](https://modelcontextprotocol.io/)

**IRAM Voice** is a small Python CLI and **Model Context Protocol (MCP)** server for Linux desktops. It wraps `edge-tts` (or an optional self-hosted VoiceStudio backend) for speech synthesis, keeps a set of voice presets, and can mix a synthesized voice track into a video with `ffmpeg`. The MCP server lets AI agents trigger speech; playback uses the first available of `pw-play`, `paplay`, `aplay` or `mpv`.

> [!NOTE]
> The default engine uses `edge-tts`, which sends text to Microsoft's online service. `clone` only stores a 16 kHz mono copy of your sample and, with the edge engine, applies a fixed EQ/compressor chain to the output; `design` only picks a stock voice with pitch/rate offsets from keywords. Neither reproduces a speaker. For true neural voice cloning, connect to a VoiceStudio backend.

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
   edge-tts or         Sample storage +        Keyword-to-preset       Mix TTS track into   Stdio MCP server
   VoiceStudio TTS     fixed EQ chain          heuristics              video (ffmpeg amix)  for MCP clients
```

---

## 🌟 Key Features

1. **Speech Synthesis**:
   - Neural voices via `edge-tts` (online) or a VoiceStudio backend; playback goes through PipeWire (`pw-play`) when available, with fallbacks. If `edge-tts` is missing, `espeak` is used when installed.
   - Select between `edge` (default, online Microsoft service), `voicestudio` (self-hosted backend), or `auto` fallback mode.
2. **Preset Voice Profiling & Design**:
   - `clone`: Converts the sample to 16 kHz mono WAV and registers a profile. The reference audio is only used for a fixed bass/treble/compressor filter on edge output; it is not sent to VoiceStudio and does not reproduce the speaker.
   - `design`: Keyword matching on the description (e.g. deep/high, fast/slow, male/female, tamil) picks pitch, rate and a stock edge voice.
3. **Model Context Protocol (MCP) Server**:
   - Standard JSON-RPC stdio transport. Exposes `generate_speech`, `clone_voice`, `design_voice`, `list_voices` and `check_health`. It implements only the MCP 2024-11-05 `initialize` and `tools/*` requests (no resources, prompts or notification handling). Compatibility with specific clients has not been verified. `check_health` currently returns a static status and does not probe PipeWire or the backends.
4. **Video Dubbing with Auto-Ducking**:
   - Lowers the original audio to 35% volume (about -9 dB, constant for the whole clip, not sidechain ducking) and mixes in one synthesized track starting at t=0 with `amix`; the output is AAC audio with the video stream copied. There is no timing alignment, and the source video must have an audio track.
5. **Bilingual & Multi-Language**:
   - Ships presets for English (`jarvis`, `samantha`, `cinema-narrator`, `cyber-synth`) and Tamil (`tamil-tech` / Kavitha, `tamil-male` / Valluvan), all mapped to Microsoft Edge neural voices.

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
- `VOICESTUDIO_API_KEY`: Optional API key, sent as a `Bearer` token and excluded from the client's `repr`. Use HTTPS or a private network such as Tailscale for remote servers, because plain HTTP exposes the key and your text.
- `IRAM_VOICE_ENGINE`: Set default engine (`edge`, `voicestudio`, or `auto`).

### Example Commands
```bash
# List available voices on VoiceStudio
iram-voice vs-voices

# Synthesize speech using VoiceStudio engine
iram-voice speak "Synthesizing with VoiceStudio" --engine voicestudio

# Select a voice that exists on the VoiceStudio server (--voice presets are ignored by this engine)
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
Requirements: Python 3.9+ (standard library only), `ffmpeg` (clone/dub), and for the default engine the `edge-tts` CLI (`pip install edge-tts`, or `pip install .[edge]`). Nothing else is required for the VoiceStudio engine.

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

# Store a reference sample (EQ only, no real cloning)
iram-voice clone /path/to/sample.wav --name "MyVoice" --gender male

# Design a synthetic persona
iram-voice design "deep calm cyberpunk detective" --name "K-2049"

# Mix a synthesized voice track into a video
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

## 🧪 Development
See [CONTRIBUTING.md](CONTRIBUTING.md). Security reports: [SECURITY.md](SECURITY.md).

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

---

## 📜 License
MIT License. Created by [Pravin](https://github.com/apravint) for IRAM OS.
