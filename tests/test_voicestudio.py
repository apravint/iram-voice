import os
import sys
import io
import json
import tempfile
import threading
import unittest
from unittest import mock
import http.server

from iram_voice.core import VoiceStudioClient, VoiceStudioEngine, format_from_path


class FakeVoiceStudioHandler(http.server.BaseHTTPRequestHandler):
    """Local HTTP handler simulating the VoiceStudio API contract."""

    def log_message(self, format, *args):
        # Silence HTTP access logs during test runs
        pass

    def do_GET(self):
        self.server.last_request = {
            "method": "GET",
            "path": self.path,
            "headers": dict(self.headers),
        }
        if self.path == "/v1/audio/voices":
            status = getattr(self.server, "voices_status", 200)
            body = getattr(self.server, "voices_body", {
                "voices": [
                    {
                        "id": "studio-voice-1",
                        "voice_id": "studio-voice-1",
                        "name": "Studio Voice",
                        "type": "profile",
                        "language": "en-US",
                        "description": "High fidelity studio voice",
                    }
                ],
                "engines": ["omnivoice"],
            })
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            data = json.dumps(body).encode("utf-8") if isinstance(body, (dict, list)) else body
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            body_json = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            body_json = None

        self.server.last_request = {
            "method": "POST",
            "path": self.path,
            "headers": dict(self.headers),
            "body_json": body_json,
            "body_bytes": body_bytes,
        }

        if self.path == "/v1/audio/speech":
            status = getattr(self.server, "speech_status", 200)
            if status == 200:
                audio_data = getattr(self.server, "speech_body", b"FAKE_AUDIO_DATA_MP3")
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(audio_data)))
                self.end_headers()
                self.wfile.write(audio_data)
            else:
                err_data = getattr(
                    self.server,
                    "speech_body",
                    {"error": {"message": "Invalid speech request", "type": "invalid_request_error"}},
                )
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                out_bytes = json.dumps(err_data).encode("utf-8") if isinstance(err_data, dict) else err_data
                self.send_header("Content-Length", str(len(out_bytes)))
                self.end_headers()
                self.wfile.write(out_bytes)
        else:
            self.send_response(404)
            self.end_headers()


class FakeVoiceStudioServer:
    """Manages the lifecycle of a local HTTP server simulating VoiceStudio."""

    def __init__(self):
        self.server = http.server.HTTPServer(("127.0.0.1", 0), FakeVoiceStudioHandler)
        self.server.last_request = None
        self.server.speech_status = 200
        self.server.speech_body = b"FAKE_AUDIO_DATA_MP3"
        self.server.voices_status = 200
        self.server.voices_body = {
            "voices": [
                {
                    "id": "studio-voice-1",
                    "voice_id": "studio-voice-1",
                    "name": "Studio Voice",
                    "type": "profile",
                    "language": "en-US",
                }
            ],
            "engines": ["omnivoice"],
        }
        self.port = self.server.server_address[1]
        self.url = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2.0)


class TestVoiceStudioIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake_server = FakeVoiceStudioServer()

    @classmethod
    def tearDownClass(cls):
        cls.fake_server.stop()

    def setUp(self):
        self.fake_server.server.speech_status = 200
        self.fake_server.server.speech_body = b"FAKE_AUDIO_DATA_MP3"
        self.fake_server.server.voices_status = 200
        self.fake_server.server.voices_body = {
            "voices": [
                {
                    "id": "studio-voice-1",
                    "voice_id": "studio-voice-1",
                    "name": "Studio Voice",
                    "type": "profile",
                    "language": "en-US",
                }
            ],
            "engines": ["omnivoice"],
        }
        self.fake_server.server.last_request = None

    def test_format_from_path(self):
        self.assertEqual(format_from_path("output.mp3"), "mp3")
        self.assertEqual(format_from_path("test.wav"), "wav")
        self.assertEqual(format_from_path("/path/to/file.flac"), "flac")
        self.assertEqual(format_from_path("audio.opus"), "opus")
        self.assertEqual(format_from_path("track.ogg"), "opus")
        self.assertEqual(format_from_path("sound.aac"), "aac")
        self.assertEqual(format_from_path("clip.m4a"), "aac")
        self.assertEqual(format_from_path("raw.pcm"), "pcm")
        self.assertEqual(format_from_path("unknown.xyz"), "mp3")

    def test_success_synthesis(self):
        client = VoiceStudioClient(base_url=self.fake_server.url)
        audio = client.synthesize("Hello world", voice="studio-voice-1", response_format="wav")
        self.assertEqual(audio, b"FAKE_AUDIO_DATA_MP3")

        last_req = self.fake_server.server.last_request
        self.assertIsNotNone(last_req)
        self.assertEqual(last_req["method"], "POST")
        self.assertEqual(last_req["path"], "/v1/audio/speech")
        self.assertEqual(last_req["body_json"]["model"], "omnivoice")
        self.assertEqual(last_req["body_json"]["input"], "Hello world")
        self.assertEqual(last_req["body_json"]["voice"], "studio-voice-1")
        self.assertEqual(last_req["body_json"]["response_format"], "wav")

    def test_engine_synthesize_voicestudio(self):
        client = VoiceStudioClient(base_url=self.fake_server.url)
        engine = VoiceStudioEngine(vs_client=client)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            out = engine.synthesize(
                "Testing VoiceStudio engine",
                output_path=tmp_path,
                engine="voicestudio",
                vs_voice="studio-voice-1",
            )
            self.assertEqual(out, tmp_path)
            with open(tmp_path, "rb") as f:
                content = f.read()
            self.assertEqual(content, b"FAKE_AUDIO_DATA_MP3")

            last_req = self.fake_server.server.last_request
            self.assertEqual(last_req["body_json"]["voice"], "studio-voice-1")
            self.assertEqual(last_req["body_json"]["response_format"], "wav")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_success_voices(self):
        client = VoiceStudioClient(base_url=self.fake_server.url)
        voices = client.list_voices()
        self.assertEqual(len(voices), 1)
        self.assertEqual(voices[0]["id"], "studio-voice-1")
        self.assertEqual(voices[0]["name"], "Studio Voice")

        engine = VoiceStudioEngine(vs_client=client)
        engine_voices = engine.list_vs_voices()
        self.assertEqual(len(engine_voices), 1)
        self.assertEqual(engine_voices[0]["name"], "Studio Voice")

    def test_api_error(self):
        self.fake_server.server.speech_status = 400
        self.fake_server.server.speech_body = {
            "error": {
                "message": "Model 'invalid_model' not found",
                "type": "invalid_request_error",
                "param": "model",
                "code": "model_not_found",
            }
        }

        client = VoiceStudioClient(base_url=self.fake_server.url)
        with self.assertRaises(RuntimeError) as ctx:
            client.synthesize("Fail this request")
        self.assertIn("VoiceStudio API error (400)", str(ctx.exception))
        self.assertIn("Model 'invalid_model' not found", str(ctx.exception))

        engine = VoiceStudioEngine(vs_client=client)
        with self.assertRaises(RuntimeError) as ctx:
            engine.synthesize("Fail in engine", engine="voicestudio")
        self.assertIn("VoiceStudio API error (400)", str(ctx.exception))

    def test_server_unreachable_error(self):
        # Point to an unreachable local port
        unreachable_client = VoiceStudioClient(base_url="http://127.0.0.1:1")
        engine = VoiceStudioEngine(vs_client=unreachable_client)

        with self.assertRaises(RuntimeError) as ctx:
            engine.synthesize("Will fail unreachable", engine="voicestudio")
        self.assertIn("unreachable", str(ctx.exception).lower())

    def test_auth_header_sent_and_not_logged(self):
        api_key = "secret_vs_token_98765"
        client = VoiceStudioClient(base_url=self.fake_server.url, api_key=api_key)

        client.synthesize("Authenticated hello")
        last_req = self.fake_server.server.last_request
        self.assertEqual(last_req["headers"].get("Authorization"), f"Bearer {api_key}")

        client.get_voices()
        last_req = self.fake_server.server.last_request
        self.assertEqual(last_req["headers"].get("Authorization"), f"Bearer {api_key}")

        # Ensure API key is never in __repr__
        repr_str = repr(client)
        self.assertNotIn(api_key, repr_str)

    def test_auth_header_absent_when_not_provided(self):
        client = VoiceStudioClient(base_url=self.fake_server.url, api_key=None)
        client.synthesize("No auth")
        last_req = self.fake_server.server.last_request
        self.assertNotIn("Authorization", last_req["headers"])

    def test_auto_fallback_success(self):
        client = VoiceStudioClient(base_url=self.fake_server.url)
        engine = VoiceStudioEngine(vs_client=client)

        with mock.patch.object(engine, "_synthesize_edge") as mock_edge:
            stderr_trap = io.StringIO()
            with mock.patch("sys.stderr", stderr_trap):
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    out = engine.synthesize("Auto success test", output_path=tmp_path, engine="auto")
                    self.assertEqual(out, tmp_path)
                    mock_edge.assert_not_called()
                    self.assertEqual(stderr_trap.getvalue(), "")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

    def test_auto_fallback_on_unreachable(self):
        unreachable_client = VoiceStudioClient(base_url="http://127.0.0.1:1")
        engine = VoiceStudioEngine(vs_client=unreachable_client)

        with mock.patch.object(engine, "_synthesize_edge", return_value="/fake/fallback.mp3") as mock_edge:
            stderr_trap = io.StringIO()
            with mock.patch("sys.stderr", stderr_trap):
                out = engine.synthesize("Auto fallback test", engine="auto")
                self.assertEqual(out, "/fake/fallback.mp3")
                mock_edge.assert_called_once()
                warning_output = stderr_trap.getvalue()
                self.assertIn("Warning: VoiceStudio failed", warning_output)
                self.assertIn("falling back to edge", warning_output)
                # Verify exactly one warning was emitted
                self.assertEqual(warning_output.count("Warning: VoiceStudio failed"), 1)

    def test_auto_fallback_on_api_error(self):
        self.fake_server.server.speech_status = 500
        self.fake_server.server.speech_body = {"error": {"message": "GPU failure during synthesis"}}

        client = VoiceStudioClient(base_url=self.fake_server.url)
        engine = VoiceStudioEngine(vs_client=client)

        with mock.patch.object(engine, "_synthesize_edge", return_value="/fake/fallback_500.mp3") as mock_edge:
            stderr_trap = io.StringIO()
            with mock.patch("sys.stderr", stderr_trap):
                out = engine.synthesize("Auto fallback 500 test", engine="auto")
                self.assertEqual(out, "/fake/fallback_500.mp3")
                mock_edge.assert_called_once()
                warning_output = stderr_trap.getvalue()
                self.assertIn("Warning: VoiceStudio failed", warning_output)
                self.assertIn("falling back to edge", warning_output)
                self.assertEqual(warning_output.count("Warning: VoiceStudio failed"), 1)

    def test_no_network_to_real_services(self):
        # Verify default base_url is localhost:3900 and tests only communicate with the local fake server
        client = VoiceStudioClient()
        self.assertEqual(client.base_url, "http://localhost:3900")
        self.assertTrue(self.fake_server.url.startswith("http://127.0.0.1:"))


if __name__ == "__main__":
    unittest.main()
