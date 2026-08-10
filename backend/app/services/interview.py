from datetime import datetime, timezone
from uuid import uuid4
from app.schemas import Feedback, InterviewSession
from app.seed import ML_KNOWLEDGE


class InterviewService:
    def __init__(self, store, evaluator, total_questions: int = 5):
        self.store, self.evaluator, self.total_questions = store, evaluator, total_questions
        self.sessions: dict[str, InterviewSession] = {}

    def start(self, topic: str, user_id: str) -> InterviewSession:
        question = ML_KNOWLEDGE[0]["question"]
        session = InterviewSession(id=str(uuid4()), user_id=user_id, topic=topic, question=question, question_number=1, total_questions=self.total_questions, created_at=datetime.now(timezone.utc))
        self.sessions[session.id] = session
        return session

    def get(self, session_id: str) -> InterviewSession:
        if session_id not in self.sessions: raise KeyError("Interview session not found.")
        return self.sessions[session_id]

    def answer(self, session_id: str, transcript: str) -> tuple[InterviewSession, Feedback]:
        if not transcript.strip(): raise ValueError("Transcript cannot be empty.")
        session = self.get(session_id)
        knowledge, memory = self.store.retrieve_context(f"{session.question} {transcript}", session.user_id)
        feedback = self.evaluator.evaluate(session.question, transcript, knowledge, memory)
        feedback.relevant_concept = knowledge[0].get("title") if knowledge else None
        self.store.store_memory(session.user_id, session.id, session.topic, feedback)
        self.store.store_history(session.user_id, session.id, session.question, transcript, feedback)
        session.transcript, session.feedback = transcript.strip(), feedback
        return session, feedback

    def next_question(self, session_id: str) -> InterviewSession:
        session = self.get(session_id)
        if not session.feedback: raise ValueError("Submit an answer before requesting the next question.")
        if session.question_number >= session.total_questions: session.completed = True; return session
        weakness_query = " ".join(session.feedback.weaknesses + session.feedback.missing_concepts) or session.topic
        knowledge, memory = self.store.retrieve_context(weakness_query, session.user_id)
        question = session.feedback.recommended_next_question or (knowledge[0].get("question") if knowledge else ML_KNOWLEDGE[session.question_number % len(ML_KNOWLEDGE)]["question"])
        if memory and memory[0].get("weaknesses"): question = f"Building on an earlier weakness ({memory[0]['weaknesses'][0]}): {question}"
        session.question, session.question_number, session.transcript, session.feedback = question, session.question_number + 1, "", None
        return session

    def end(self, session_id: str) -> InterviewSession:
        session = self.get(session_id); session.completed = True; return session
