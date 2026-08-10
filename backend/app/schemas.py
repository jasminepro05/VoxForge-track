from datetime import datetime
from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=120)
    user_id: str = Field(default="anonymous", min_length=1, max_length=120)


class AnswerRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=12000)


class Feedback(BaseModel):
    score: int = Field(ge=0, le=100)
    correctness: str
    summary: str
    strengths: list[str] = []
    weaknesses: list[str] = []
    missing_concepts: list[str] = []
    relevant_concept: str | None = None
    recommended_next_question: str | None = None


class InterviewSession(BaseModel):
    id: str
    user_id: str
    topic: str
    question: str
    question_number: int
    total_questions: int
    transcript: str = ""
    feedback: Feedback | None = None
    completed: bool = False
    created_at: datetime


class AnswerResponse(BaseModel):
    session: InterviewSession
    feedback: Feedback


class HealthResponse(BaseModel):
    status: str


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4096)


class TranscriptionResponse(BaseModel):
    transcript: str


class SpeechResponse(BaseModel):
    audioBase64: str
    audioContentType: str
