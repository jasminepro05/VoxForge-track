import json
from google import genai
from google.genai import types
from app.config import Settings
from app.schemas import Feedback


class GeminiEvaluator:
    def __init__(self, settings: Settings):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for answer evaluation.")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def evaluate(self, question: str, transcript: str, knowledge: list[dict], memory: list[dict]) -> Feedback:
        prompt = f"""You evaluate a machine-learning interview answer. Return JSON only with score (0-100), correctness, summary, strengths, weaknesses, missing_concepts, recommended_next_question.\nQuestion: {question}\nAnswer: {transcript}\nRetrieved knowledge: {knowledge}\nPast weakness memory: {memory}"""
        try:
            response = self.client.models.generate_content(model=self.model, contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
            payload = json.loads(response.text)
            return Feedback(**payload)
        except Exception as error:
            raise RuntimeError(f"Gemini evaluation failed: {error}") from error
