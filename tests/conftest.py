"""Isolate tests from the real home directory.

iram_voice.core reads HOME at import time to locate profiles and cache, so
this must run before the module is first imported.
"""
import os
import tempfile

_TMP_HOME = tempfile.mkdtemp(prefix="iram-voice-test-home-")
os.environ["HOME"] = _TMP_HOME
os.environ.pop("IRAM_VOICE_ENGINE", None)
