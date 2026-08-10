import base64
import json
import httpx
from app.config import Settings
from app.services.voice import VoiceService


def client_for(handler):
    return httpx.Client(transport=httpx.MockTransport(handler), base_url="https://voice.test")


def test_transcribe_forwards_audio_to_openai_compatible_provider():
    def handler(request):
        assert request.headers["authorization"] == "Bearer stt-token"
        assert b'name="model"' in request.content
        assert b'answer.webm' in request.content
        return httpx.Response(200, json={"text": "  Explain regularization. "})
    settings = Settings(stt_api_key="stt-token", stt_api_url="https://voice.test/transcribe")
    assert VoiceService(settings, client_for(handler)).transcribe("answer.webm", "audio/webm", b"audio") == "Explain regularization."


def test_synthesize_returns_browser_playable_base64_audio():
    def handler(request):
        assert request.headers["authorization"] == "Bearer rime-token"
        assert json.loads(request.content) == {"text": "Hello", "speaker": "celeste", "modelId": "coda"}
        return httpx.Response(200, content=b"RIFF-data", headers={"content-type": "audio/wav"})
    settings = Settings(rime_api_key="rime-token", rime_api_url="https://voice.test/rime")
    content, content_type = VoiceService(settings, client_for(handler)).synthesize("Hello")
    assert content_type == "audio/wav"
    assert base64.b64decode(content) == b"RIFF-data"
