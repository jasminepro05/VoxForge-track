# VoxMock

Voice-based, adaptive technical-interview practice. The React client records answers and plays interviewer speech; the FastAPI service evaluates answers with Gemini and uses Qdrant to retain learning context.

## Start locally

1. Copy `.env.example` to `.env` and provide `GEMINI_API_KEY`. To use microphone features, also set `STT_API_KEY` and `RIME_API_KEY`. Start Qdrant at the configured `QDRANT_URL`.
2. In `backend/`, install requirements and run `uvicorn app.main:app --reload`.
3. In `frontend/`, install dependencies and run `npm run dev` (or `pnpm dev`). The Vite proxy forwards `/api` requests to `http://127.0.0.1:8000`.

The backend health check is available at `http://127.0.0.1:8000/health`. An interview cannot run until Gemini and Qdrant are configured.
