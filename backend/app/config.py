from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "gemini-embedding-001"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_knowledge_collection: str = "voxmock_technical_knowledge"
    qdrant_memory_collection: str = "voxmock_user_memory"
    qdrant_history_collection: str = "voxmock_interview_history"
    cors_origins: str = "http://localhost:5173"
    rime_api_key: str | None = None
    rime_api_url: str = "https://users.rime.ai/v1/rime-tts"
    rime_speaker: str = "celeste"
    rime_model: str = "coda"
    stt_provider: str = "openai"
    stt_api_key: str | None = None
    stt_api_url: str = "https://api.openai.com/v1/audio/transcriptions"
    stt_model: str = "gpt-4o-mini-transcribe"
    voice_max_upload_bytes: int = 25 * 1024 * 1024

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
