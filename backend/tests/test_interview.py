from app.schemas import Feedback
from app.services.interview import InterviewService

class FakeStore:
    def __init__(self): self.memories = []
    def retrieve_context(self, text, user_id): return ([{"title":"Data leakage", "question":"How do you prevent data leakage?"}], self.memories)
    def store_memory(self, user_id, session_id, topic, feedback): self.memories.append({"weaknesses": feedback.weaknesses})
    def store_history(self, *args): pass
class FakeEvaluator:
    def evaluate(self, *args): return Feedback(score=55, correctness="partially correct", summary="Explain leakage prevention.", strengths=["identified splitting"], weaknesses=["preprocessing leakage"], missing_concepts=["fit transforms on training folds"], recommended_next_question=None)

def test_answer_stores_memory_and_adapts_next_question():
    service = InterviewService(FakeStore(), FakeEvaluator(), total_questions=2)
    session = service.start("machine learning", "candidate-1")
    answered, feedback = service.answer(session.id, "I would split the dataset.")
    assert feedback.score == 55 and answered.feedback is feedback
    next_session = service.next_question(session.id)
    assert next_session.question_number == 2
    assert "earlier weakness" in next_session.question

def test_empty_transcript_is_rejected():
    service = InterviewService(FakeStore(), FakeEvaluator())
    session = service.start("machine learning", "candidate-1")
    try: service.answer(session.id, "   ")
    except ValueError as error: assert "empty" in str(error).lower()
    else: raise AssertionError("Expected empty transcript to fail")
