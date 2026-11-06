# Contributing

Thanks for helping out.

## Setup
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"      # core is stdlib-only; add ".[edge]" to run the real edge-tts engine
```

## Before opening a PR
```bash
ruff check .
pytest
```
CI runs the same on Python 3.9-3.13. Tests must not need network, `ffmpeg`, `edge-tts` or audio devices: mock `subprocess.run`, `shutil.which` and HTTP calls (see `tests/`). `tests/conftest.py` redirects `HOME` to a temp dir so tests never touch your real voice profiles.

## Guidelines
- Keep the core dependency-free; heavy or optional tooling goes in an extra in `pyproject.toml`.
- README claims must match the code. If you change behaviour, update the README in the same PR.
- Real voice cloning needs the speaker's consent; do not add features that bypass that.
- Keep PRs small and describe how you verified them.
