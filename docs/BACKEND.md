# VoxMock backend

Run from `backend/` after copying the root `.env.example` to `.env` and supplying the required keys:

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The startup process validates `GEMINI_API_KEY`, creates/seeds three Qdrant collections, and uses Gemini embeddings for every stored and queried vector.

## APIs

`POST /api/interview/start` accepts `{ "topic": "machine learning", "user_id": "optional-user" }` and returns a session/question.

`POST /api/interview/{session_id}/answer` accepts `{ "transcript": "..." }`, retrieves technical knowledge plus that user's past weaknesses from Qdrant, asks Gemini for structured feedback, then stores memory and history in Qdrant.

`POST /api/interview/{session_id}/next`, `GET /api/interview/{session_id}`, and `POST /api/interview/{session_id}/end` advance, read, and finish a session. Plural `/api/interviews` aliases are provided for the existing frontend client.

The voice layer should transcribe audio first, then send its final text to the answer endpoint. Rime/STT proxy endpoints remain a separate voice-backend concern; this service consumes the transcript and produces adaptive interview data.

## Voice endpoints

`POST /api/voice/transcriptions` accepts a multipart `audio` upload (up to 25 MB) and returns `{ "transcript": "..." }`. It uses the OpenAI-compatible transcription endpoint configured through `STT_*` settings.

`POST /api/voice/speech` accepts `{ "text": "..." }` and returns base64-encoded Rime WAV audio. Set `RIME_API_KEY`; `RIME_SPEAKER` defaults to `celeste` and `RIME_MODEL` to `coda`.

## Qdrant collections

- `voxmock_technical_knowledge`: seeded ML concepts and question candidates.
- `voxmock_user_memory`: semantic, per-user weakness/strength memory used when selecting the next question.
- `voxmock_interview_history`: answer/performance records for long-term retrieval and analytics.
