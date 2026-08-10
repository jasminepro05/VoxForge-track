from google import genai
from google.genai import types
from app.config import Settings


class GeminiEmbeddingProvider:
    dimension = 768

    def __init__(self, settings: Settings):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for embeddings.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_embedding_model

    def embed(self, text: str, document: bool = False) -> list[float]:
        task = "RETRIEVAL_DOCUMENT" if document else "RETRIEVAL_QUERY"
        response = self.client.models.embed_content(model=self.model, contents=text, config=types.EmbedContentConfig(task_type=task, output_dimensionality=self.dimension))
        return list(response.embeddings[0].values)
