const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error'
export type VoiceErrorCode = 'permission-denied' | 'microphone-unavailable' | 'empty-speech' | 'stt-failed' | 'rime-failed' | 'network-failed' | 'playback-failed'

export class VoiceError extends Error {
  constructor(readonly code: VoiceErrorCode, message: string, readonly cause?: unknown) {
    super(message)
    this.name = 'VoiceError'
  }
}

export interface VoiceCallbacks {
  onTranscript: (text: string) => void
  onState: (state: VoiceState) => void
  onError: (error: VoiceError) => void
  onSpeechEnd?: () => void
}

interface SpeechResponse {
  audioUrl?: string
  audioBase64?: string
  audioContentType?: string
}

interface TranscriptionResponse { transcript: string }

function voiceEndpoint(path: string) { return `${BASE_URL}${path}` }

async function readError(response: Response, fallback: string) {
  try {
    const body = await response.json() as { detail?: string; message?: string }
    return body.detail || body.message || fallback
  } catch { return fallback }
}

async function transcribe(audio: Blob, signal: AbortSignal): Promise<string> {
  const form = new FormData()
  form.append('audio', audio, `answer.${audio.type.includes('ogg') ? 'ogg' : 'webm'}`)
  let response: Response
  try { response = await fetch(voiceEndpoint('/api/voice/transcriptions'), { method: 'POST', body: form, signal }) }
  catch (cause) { throw new VoiceError('network-failed', 'Speech transcription could not reach the server.', cause) }
  if (!response.ok) throw new VoiceError('stt-failed', await readError(response, 'Speech transcription failed.'))
  const { transcript } = await response.json() as TranscriptionResponse
  if (!transcript?.trim()) throw new VoiceError('empty-speech', 'No speech was detected. Please try again.')
  return transcript.trim()
}

async function requestRimeAudio(text: string, signal: AbortSignal): Promise<{ src: string; revoke: boolean }> {
  let response: Response
  try {
    response = await fetch(voiceEndpoint('/api/voice/speech'), {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }), signal,
    })
  } catch (cause) { throw new VoiceError('network-failed', 'Rime voice generation could not reach the server.', cause) }
  if (!response.ok) throw new VoiceError('rime-failed', await readError(response, 'Rime voice generation failed.'))
  const body = await response.json() as SpeechResponse
  if (body.audioUrl) return { src: body.audioUrl, revoke: false }
  if (body.audioBase64) return { src: `data:${body.audioContentType ?? 'audio/mpeg'};base64,${body.audioBase64}`, revoke: false }
  throw new VoiceError('rime-failed', 'Rime did not return playable audio.')
}

/** Browser-side voice orchestration. API keys never enter this module. */
export function createVoiceController(callbacks: VoiceCallbacks) {
  let recorder: MediaRecorder | undefined
  let stream: MediaStream | undefined
  let audio: HTMLAudioElement | undefined
  let request: AbortController | undefined
  let stoppedByUser = false

  const setState = (state: VoiceState) => callbacks.onState(state)
  const releaseMicrophone = () => { stream?.getTracks().forEach(track => track.stop()); stream = undefined }
  const report = (error: VoiceError) => { setState('error'); callbacks.onError(error) }

  async function finishRecording() {
    if (!recorder) return
    const activeRecorder = recorder
    const chunks = (activeRecorder as MediaRecorder & { voxmockChunks?: BlobPart[] }).voxmockChunks ?? []
    activeRecorder.addEventListener('stop', async () => {
      recorder = undefined
      releaseMicrophone()
      if (stoppedByUser) return
      const blob = new Blob(chunks, { type: activeRecorder.mimeType || 'audio/webm' })
      if (!blob.size) { report(new VoiceError('empty-speech', 'No audio was captured. Please try again.')); return }
      const pending = new AbortController(); request = pending; setState('processing')
      try { callbacks.onTranscript(await transcribe(blob, pending.signal)); setState('idle') }
      catch (cause) { if (!(cause instanceof DOMException && cause.name === 'AbortError')) report(cause instanceof VoiceError ? cause : new VoiceError('stt-failed', 'Speech transcription failed.', cause)) }
      finally { if (request === pending) request = undefined }
    }, { once: true })
    activeRecorder.stop()
  }

  function interrupt() {
    stoppedByUser = true
    request?.abort(); request = undefined
    if (recorder?.state === 'recording') recorder.stop()
    recorder = undefined; releaseMicrophone()
    if (audio) { audio.pause(); audio.currentTime = 0; audio.src = ''; audio = undefined }
  }

  return {
    supported: typeof window !== 'undefined' && Boolean(window.MediaRecorder && navigator.mediaDevices?.getUserMedia),
    async start() {
      interrupt()
      if (!(window.MediaRecorder && navigator.mediaDevices?.getUserMedia)) { report(new VoiceError('microphone-unavailable', 'Audio recording is not supported by this browser.')); return }
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } })
        stoppedByUser = false
        const chunks: BlobPart[] = []
        recorder = new MediaRecorder(stream)
        recorder.addEventListener('dataavailable', event => { if (event.data.size) chunks.push(event.data) })
        // Keep chunks on the recorder instance so stop can transcribe every slice.
        ;(recorder as MediaRecorder & { voxmockChunks?: BlobPart[] }).voxmockChunks = chunks
        recorder.start(250)
        setState('listening')
      } catch (cause) {
        const denied = cause instanceof DOMException && (cause.name === 'NotAllowedError' || cause.name === 'SecurityError')
        report(new VoiceError(denied ? 'permission-denied' : 'microphone-unavailable', denied ? 'Microphone permission was denied. Enable it in your browser settings and try again.' : 'The microphone is unavailable. Check that no other app is using it.', cause))
      }
    },
    stop() { if (recorder?.state === 'recording') void finishRecording() },
    interrupt,
    async speak(text: string) {
      interrupt()
      if (!text.trim()) return
      const pending = new AbortController(); request = pending; setState('processing')
      try {
        const source = await requestRimeAudio(text, pending.signal)
        if (pending.signal.aborted) return
        audio = new Audio(source.src)
        const currentAudio = audio
        audio.addEventListener('ended', () => { if (audio === currentAudio) { audio = undefined; setState('idle'); callbacks.onSpeechEnd?.() } }, { once: true })
        audio.addEventListener('error', () => report(new VoiceError('playback-failed', 'The generated Rime audio could not be played.')), { once: true })
        setState('speaking')
        await audio.play()
      } catch (cause) {
        if (!(cause instanceof DOMException && cause.name === 'AbortError')) report(cause instanceof VoiceError ? cause : new VoiceError('playback-failed', 'Audio playback failed.', cause))
      } finally { if (request === pending) request = undefined }
    },
  }
}
