import json
import os
import unittest
from unittest import mock

from iram_voice import core
from iram_voice.core import DEFAULT_PROFILES, VoiceStudioClient, VoiceStudioEngine, format_from_path
from iram_voice.mcp_server import VoiceStudioMCPServer


class TestFormatFromPath(unittest.TestCase):
    def test_known_extensions(self):
        self.assertEqual(format_from_path("a.wav"), "wav")
        self.assertEqual(format_from_path("a.OGG"), "opus")
        self.assertEqual(format_from_path("a.m4a"), "aac")

    def test_unknown_defaults_to_mp3(self):
        self.assertEqual(format_from_path("a.xyz"), "mp3")
        self.assertEqual(format_from_path("noext"), "mp3")


class TestClientConfig(unittest.TestCase):
    def test_trailing_slash_stripped(self):
        self.assertEqual(VoiceStudioClient("http://h:1/").base_url, "http://h:1")

    def test_env_url_and_key(self):
        with mock.patch.dict(os.environ, {"VOICESTUDIO_URL": "http://env:9", "VOICESTUDIO_API_KEY": "k"}):
            c = VoiceStudioClient()
        self.assertEqual(c.base_url, "http://env:9")
        self.assertEqual(c._headers()["Authorization"], "Bearer k")

    def test_no_key_no_auth_header_and_repr_hides_key(self):
        c = VoiceStudioClient("http://h", api_key=None)
        with mock.patch.dict(os.environ, clear=False):
            os.environ.pop("VOICESTUDIO_API_KEY", None)
            self.assertNotIn("Authorization", VoiceStudioClient("http://h")._headers())
        c.api_key = "secret"
        self.assertNotIn("secret", repr(c))


class EngineTestBase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(core, "PROFILES_FILE", os.path.join(core.VOICE_DIR, "t_profiles.json"))
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(lambda: os.path.exists(core.PROFILES_FILE) and os.remove(core.PROFILES_FILE))
        self.engine = VoiceStudioEngine(vs_client=VoiceStudioClient("http://127.0.0.1:1"))


class TestProfiles(EngineTestBase):
    def test_defaults_registered_and_persisted(self):
        ids = {v["id"] for v in self.engine.list_voices()}
        self.assertTrue({p["id"] for p in DEFAULT_PROFILES} <= ids)
        with open(core.PROFILES_FILE, encoding="utf-8") as f:
            self.assertTrue(ids <= set(json.load(f)))

    def test_corrupt_profiles_file_recovers(self):
        with open(core.PROFILES_FILE, "w", encoding="utf-8") as f:
            f.write("{not json")
        engine = VoiceStudioEngine(vs_client=VoiceStudioClient("http://127.0.0.1:1"))
        self.assertIn("jarvis", engine.profiles)


class TestDesignVoice(EngineTestBase):
    def test_deep_calm_male_default(self):
        p = self.engine.design_voice("deep calm detective", "K-2049")
        self.assertEqual(p["id"], "design-k-2049")
        self.assertEqual(p["gender"], "male")
        self.assertEqual(p["pitch"], "-10Hz")
        self.assertEqual(p["rate"], "-10%")
        self.assertEqual(p["voice_model"], "en-US-EricNeural")

    def test_high_fast_female(self):
        p = self.engine.design_voice("young energetic woman", "Spark")
        self.assertEqual(p["gender"], "female")
        self.assertEqual(p["pitch"], "+8Hz")
        self.assertEqual(p["rate"], "+15%")
        self.assertEqual(p["voice_model"], "en-US-AriaNeural")

    def test_tamil_switches_model_and_lang(self):
        p = self.engine.design_voice("tamil female narrator", "Thendral")
        self.assertEqual(p["lang"], "ta-IN")
        self.assertEqual(p["voice_model"], "ta-IN-PallaviNeural")

    def test_persisted_and_listed(self):
        self.engine.design_voice("neutral", "Zed")
        self.assertIn("design-zed", {v["id"] for v in self.engine.list_voices()})


class TestCloneVoice(EngineTestBase):
    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            self.engine.clone_voice("/nonexistent/sample.wav", "X")

    def test_clone_calls_ffmpeg_and_stores_profile(self):
        sample = os.path.join(core.VOICE_DIR, "t_sample.wav")
        with open(sample, "wb") as f:
            f.write(b"x")
        self.addCleanup(os.remove, sample)
        with mock.patch.object(core.subprocess, "run") as run:
            p = self.engine.clone_voice(sample, "My Voice!", gender="male")
        self.assertEqual(p["id"], "clone-my-voice")
        self.assertEqual(p["engine"], "cloned")
        self.assertEqual(p["voice_model"], "en-US-ChristopherNeural")
        cmd = run.call_args[0][0]
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("16000", cmd)


class TestSynthesizeRouting(EngineTestBase):
    def test_unknown_engine_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.synthesize("hi", engine="bogus", output_path="/tmp/x.mp3")

    def test_env_selects_engine(self):
        with mock.patch.dict(os.environ, {"IRAM_VOICE_ENGINE": "voicestudio"}):
            with mock.patch.object(self.engine, "_synthesize_voicestudio", return_value="vs") as vs:
                self.assertEqual(self.engine.synthesize("hi", output_path="/tmp/x.mp3"), "vs")
        vs.assert_called_once()

    def test_default_is_edge(self):
        os.environ.pop("IRAM_VOICE_ENGINE", None)
        with mock.patch.object(self.engine, "_synthesize_edge", return_value="edge") as edge:
            self.assertEqual(self.engine.synthesize("hi", output_path="/tmp/x.mp3"), "edge")
        edge.assert_called_once()

    def test_edge_without_any_backend_raises(self):
        with mock.patch.object(core.shutil, "which", return_value=None), \
                mock.patch.object(core.os.path, "exists", return_value=False):
            with self.assertRaises(RuntimeError):
                self.engine._synthesize_edge("hi", "jarvis", "/tmp/x.mp3")

    def test_dub_missing_video(self):
        with self.assertRaises(FileNotFoundError):
            self.engine.dub_video("/nonexistent.mp4", "hi", "jarvis", "/tmp/out.mp4")


class TestMCPServer(EngineTestBase):
    def setUp(self):
        super().setUp()
        self.server = VoiceStudioMCPServer()
        self.server.engine = self.engine

    def call(self, method, params=None, msg_id=1):
        return self.server.handle_request({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}})

    def test_initialize(self):
        r = self.call("initialize")
        self.assertEqual(r["result"]["protocolVersion"], "2024-11-05")
        self.assertEqual(r["id"], 1)

    def test_tools_list_names(self):
        names = {t["name"] for t in self.call("tools/list")["result"]["tools"]}
        self.assertEqual(names, {"generate_speech", "clone_voice", "design_voice", "list_voices", "check_health"})

    def test_list_voices_tool(self):
        r = self.call("tools/call", {"name": "list_voices"})
        voices = json.loads(r["result"]["content"][0]["text"])
        self.assertTrue(any(v["id"] == "jarvis" for v in voices))

    def test_design_voice_tool(self):
        r = self.call("tools/call", {"name": "design_voice", "arguments": {"prompt": "deep", "voice_name": "Dee"}})
        self.assertIn("design-dee", r["result"]["content"][0]["text"])

    def test_generate_speech_tool_passes_args(self):
        with mock.patch.object(self.engine, "synthesize", return_value="/o.mp3") as syn:
            r = self.call("tools/call", {"name": "generate_speech", "arguments": {"text": "hi", "play": False}})
        syn.assert_called_once_with("hi", voice_id="jarvis", play=False)
        self.assertIn("/o.mp3", r["result"]["content"][0]["text"])

    def test_tool_error_becomes_jsonrpc_error(self):
        r = self.call("tools/call", {"name": "clone_voice", "arguments": {"audio_path": "/nope", "voice_name": "n"}})
        self.assertEqual(r["error"]["code"], -32000)

    def test_unknown_tool_and_method(self):
        self.assertEqual(self.call("tools/call", {"name": "nope"})["error"]["code"], -32601)
        self.assertEqual(self.call("bogus")["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
