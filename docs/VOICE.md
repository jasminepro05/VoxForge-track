# VoxMock voice integration

The browser records the candidate through `getUserMedia` and `MediaRecorder`. It uploads a short WebM/Ogg recording as `multipart/form-data` to `POST /api/voice/transcriptions`. The backend returns `{ "transcript": "..." }`; the frontend then sends that text through the established `POST /api/interviews/:id/answers` contract.

For interviewer speech, the frontend sends `{ "text": "..." }` to `POST /api/voice/speech`. The backend must call the Rime text-to-speech API with its server-side Rime credential. It must return either `{ "audioUrl": "https://..." }` or `{ "audioBase64": "...", "audioContentType": "audio/mpeg" }`. The client plays that Rime-produced audio with `HTMLAudioElement`; it does not use `window.speechSynthesis`.

## Backend configuration

Keep these only in backend environment configuration, never in Vite variables or browser code:

```env
RIME_API_KEY=...
STT_API_KEY=...
STT_PROVIDER=...
```

`STT_PROVIDER` may be the backend's configured provider (for example OpenAI Whisper, Deepgram, or a self-hosted service). The browser is deliberately provider-agnostic. The frontend optionally uses `VITE_API_BASE_URL` in deployments; during local development it uses the existing `/api` proxy and optional `VITE_API_PROXY_TARGET`.

## States and interruption

The controller emits `idle`, `listening`, `processing`, `speaking`, and `error`. Permission refusal, silent/empty audio, STT errors, Rime/API errors, network failures, and playback failures have distinct user-facing errors.

Selecting **Interrupt & answer** while the interviewer speaks immediately pauses and clears the active Rime audio, aborts outstanding voice network work, releases any microphone stream, and begins a new recording. This ensures a candidate can take the floor without waiting for generated speech to finish.

## Browser test checklist

Use HTTPS (or localhost) and verify: microphone permission prompt; a final transcript after **Finish answer**; the interview answer request; Rime audio playback; interruption during playback; denied permission; and a backend failure response from both voice endpoints.
