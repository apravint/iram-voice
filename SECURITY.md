# Security Policy

## Reporting a vulnerability
Please report privately via GitHub's "Report a vulnerability" (Security tab) on this repository rather than a public issue. Include steps to reproduce and affected versions. This is a personal project, so responses are best-effort.

## Things to know
- **Data leaves your machine.** The default `edge` engine sends the text to Microsoft's online service. The `voicestudio` engine sends text to the server in `VOICESTUDIO_URL`; use HTTPS or a private network, since plain HTTP exposes the text and the optional `VOICESTUDIO_API_KEY` (sent as a Bearer token).
- **MCP server trust.** The MCP server runs with your user's permissions. `clone_voice` reads any file path the client supplies and passes it to `ffmpeg`, and `generate_speech` runs `edge-tts`. Only connect it to clients you trust.
- **Local files.** Profiles and reference samples are stored unencrypted under `~/.local/share/iram/voices`; generated audio is cached in `~/.cache/iram/voice`.
- **Consent.** Only clone voices with the speaker's consent.
