from contextlib import asynccontextmanager
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.schemas import AnswerRequest, AnswerResponse, HealthResponse, InterviewSession, SpeechRequest, SpeechResponse, StartInterviewRequest, TranscriptionResponse
from app.services.embeddings import GeminiEmbeddingProvider
from app.services.gemini import GeminiEvaluator
from app.services.interview import InterviewService
from app.services.qdrant_store import QdrantStore
from app.services.voice import VoiceService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings(); embedder = GeminiEmbeddingProvider(settings); store = QdrantStore(settings, embedder); store.initialise()
    app.state.interviews = InterviewService(store, GeminiEvaluator(settings))
    app.state.voice = VoiceService(settings)
    yield


app = FastAPI(title="VoxMock API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def service() -> InterviewService: return app.state.interviews
def voice_service() -> VoiceService: return app.state.voice
def translate(error: Exception):
    if isinstance(error, KeyError): raise HTTPException(404, str(error))
    if isinstance(error, ValueError): raise HTTPException(422, str(error))
    raise HTTPException(503, str(error))

@app.get("/health", response_model=HealthResponse)
def health(): return {"status": "ok"}

@app.post("/api/interview/start", response_model=InterviewSession)
def start(request: StartInterviewRequest):
    try: return service().start(request.topic, request.user_id)
    except Exception as error: translate(error)

@app.post("/api/interview/{session_id}/answer", response_model=AnswerResponse)
def answer(session_id: str, request: AnswerRequest):
    try:
        session, feedback = service().answer(session_id, request.transcript)
        return {"session": session, "feedback": feedback}
    except Exception as error: translate(error)

@app.get("/api/interview/{session_id}", response_model=InterviewSession)
def get_interview(session_id: str):
    try: return service().get(session_id)
    except Exception as error: translate(error)

@app.post("/api/interview/{session_id}/next", response_model=InterviewSession)
def next_question(session_id: str):
    try: return service().next_question(session_id)
    except Exception as error: translate(error)

@app.post("/api/interview/{session_id}/end", response_model=InterviewSession)
def end(session_id: str):
    try: return service().end(session_id)
    except Exception as error: translate(error)

@app.post("/api/voice/transcriptions", response_model=TranscriptionResponse)
def transcribe(audio: UploadFile = File(...)):
    try:
        payload = audio.file.read()
        if not payload: raise ValueError("Audio upload is empty.")
        if len(payload) > get_settings().voice_max_upload_bytes: raise ValueError("Audio upload exceeds the 25 MB limit.")
        return {"transcript": voice_service().transcribe(audio.filename or "answer.webm", audio.content_type, payload)}
    except Exception as error: translate(error)
    finally: audio.file.close()

@app.post("/api/voice/speech", response_model=SpeechResponse)
def speak(request: SpeechRequest):
    try:
        audio_base64, content_type = voice_service().synthesize(request.text.strip())
        return {"audioBase64": audio_base64, "audioContentType": content_type}
    except Exception as error: translate(error)

# Compatibility aliases for the existing frontend service contract.
@app.post("/api/interviews", response_model=InterviewSession)
def legacy_start(request: StartInterviewRequest): return start(request)
@app.post("/api/interviews/{session_id}/answers", response_model=AnswerResponse)
def legacy_answer(session_id: str, request: AnswerRequest): return answer(session_id, request)
@app.post("/api/interviews/{session_id}/next", response_model=InterviewSession)
def legacy_next(session_id: str): return next_question(session_id)
@app.post("/api/interviews/{session_id}/complete", response_model=InterviewSession)
def legacy_complete(session_id: str): return end(session_id)
