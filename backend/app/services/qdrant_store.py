from uuid import NAMESPACE_URL, uuid5
from qdrant_client import QdrantClient, models
from app.config import Settings
from app.seed import ML_KNOWLEDGE


class QdrantStore:
    """All three collections affect the interview decision path, not just analytics."""
    def __init__(self, settings: Settings, embedder):
        self.settings, self.embedder = settings, embedder
        self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        self.collections = [settings.qdrant_knowledge_collection, settings.qdrant_memory_collection, settings.qdrant_history_collection]

    def initialise(self) -> None:
        try:
            for name in self.collections:
                if not self.client.collection_exists(name):
                    self.client.create_collection(name, vectors_config=models.VectorParams(size=self.embedder.dimension, distance=models.Distance.COSINE))
            self.seed_knowledge()
        except Exception as error:
            raise RuntimeError(f"Qdrant connection/setup failed: {error}") from error

    def _upsert(self, collection: str, key: str, text: str, payload: dict) -> None:
        self.client.upsert(collection_name=collection, wait=True, points=[models.PointStruct(id=str(uuid5(NAMESPACE_URL, key)), vector=self.embedder.embed(text, document=True), payload=payload | {"text": text})])

    def seed_knowledge(self) -> None:
        for item in ML_KNOWLEDGE:
            self._upsert(self.settings.qdrant_knowledge_collection, f"knowledge:{item['id']}", f"{item['title']} {item['content']}", item)

    def search(self, collection: str, text: str, limit: int = 4, user_id: str | None = None) -> list[dict]:
        query_filter = None
        if user_id:
            query_filter = models.Filter(must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=user_id))])
        result = self.client.query_points(collection_name=collection, query=self.embedder.embed(text), query_filter=query_filter, limit=limit).points
        return [point.payload | {"score": point.score} for point in result]

    def retrieve_context(self, text: str, user_id: str) -> tuple[list[dict], list[dict]]:
        return self.search(self.settings.qdrant_knowledge_collection, text), self.search(self.settings.qdrant_memory_collection, text, user_id=user_id)

    def store_memory(self, user_id: str, session_id: str, topic: str, feedback) -> None:
        text = f"Topic {topic}. Score {feedback.score}. Weaknesses: {', '.join(feedback.weaknesses + feedback.missing_concepts)}. Strengths: {', '.join(feedback.strengths)}"
        self._upsert(self.settings.qdrant_memory_collection, f"memory:{session_id}:{feedback.score}", text, {"user_id": user_id, "session_id": session_id, "topic": topic, "score": feedback.score, "weaknesses": feedback.weaknesses, "missing_concepts": feedback.missing_concepts})

    def store_history(self, user_id: str, session_id: str, question: str, transcript: str, feedback) -> None:
        self._upsert(self.settings.qdrant_history_collection, f"history:{session_id}:{question}", f"{question} {transcript} score {feedback.score}", {"user_id": user_id, "session_id": session_id, "score": feedback.score, "question": question, "weaknesses": feedback.weaknesses})
