import base64
import httpx
from app.config import Settings


class VoiceService:
    """Server-side adapters for STT and Rime; provider credentials never reach the browser."""

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.settings = settings
        self.client = client or httpx.Client(timeout=45.0)

    @staticmethod
    def _message(response: httpx.Response, fallback: str) -> str:
        try:
            detail = response.json()
            return detail.get("error", {}).get("message") or detail.get("detail") or fallback
        except (ValueError, AttributeError):
            return fallback

    def transcribe(self, filename: str, content_type: str | None, audio: bytes) -> str:
        if not self.settings.stt_api_key:
            raise RuntimeError("STT_API_KEY is required for transcription.")
        if self.settings.stt_provider.lower() != "openai":
            raise ValueError(f"Unsupported STT_PROVIDER: {self.settings.stt_provider}. Use 'openai'.")
        response = self.client.post(
            self.settings.stt_api_url,
            headers={"Authorization": f"Bearer {self.settings.stt_api_key}"},
            data={"model": self.settings.stt_model},
            files={"file": (filename or "answer.webm", audio, content_type or "audio/webm")},
        )
        if response.is_error:
            raise RuntimeError(self._message(response, "Speech transcription failed."))
        transcript = response.json().get("text", "").strip()
        if not transcript:
            raise ValueError("No speech was detected in the audio.")
        return transcript

    def synthesize(self, text: str) -> tuple[str, str]:
        if not self.settings.rime_api_key:
            raise RuntimeError("RIME_API_KEY is required for speech generation.")
        response = self.client.post(
            self.settings.rime_api_url,
            headers={"Authorization": f"Bearer {self.settings.rime_api_key}", "Accept": "audio/wav"},
            json={"text": text, "speaker": self.settings.rime_speaker, "modelId": self.settings.rime_model},
        )
        if response.is_error:
            raise RuntimeError(self._message(response, "Rime speech generation failed."))
        content_type = response.headers.get("content-type", "audio/wav").split(";", 1)[0]
        if not content_type.startswith("audio/") or not response.content:
            raise RuntimeError("Rime did not return playable audio.")
        return base64.b64encode(response.content).decode("ascii"), content_type
