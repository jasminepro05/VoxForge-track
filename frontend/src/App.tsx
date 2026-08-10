import { useMemo, useRef } from 'react'
import { ApiError, interviewApi } from './services/interviewApi'
import { createVoiceController, type VoiceError } from './services/voiceApi'
import { useSessionState } from './services/sessionState'

const statusLabel = { idle: 'Ready when you are', starting: 'Preparing your interview', listening: 'Listening…', processing: 'Thinking through your answer', speaking: 'VoxMock is speaking', feedback: 'Answer reviewed', error: 'Something needs attention', completed: 'Interview complete' }
function Icon({ name }: { name: 'mic' | 'spark' | 'arrow' | 'sound' }) { return <span className={`icon ${name}`}>{name === 'mic' ? '●' : name === 'arrow' ? '→' : name === 'sound' ? ')))' : '✦'}</span> }

export default function App() {
  const { status, setStatus, session, setSession, error, setError } = useSessionState()
  const sessionRef = useRef(session); sessionRef.current = session
  const speechPurpose = useRef<'question' | 'feedback' | null>(null)
  const submitAnswerRef = useRef<(text: string) => Promise<void>>(async () => {})
  const voice = useMemo(() => createVoiceController({
    onTranscript: text => { const active = sessionRef.current; if (active) { setSession({ ...active, transcript: text }); void submitAnswerRef.current(text) } },
    onState: state => { if (state === 'listening' || state === 'processing' || state === 'speaking' || state === 'error') setStatus(state) },
    onError: (voiceError: VoiceError) => setError(voiceError.message),
    onSpeechEnd: () => { if (speechPurpose.current === 'feedback') setStatus('feedback'); else if (speechPurpose.current === 'question') setStatus('idle'); speechPurpose.current = null },
  }), [setError, setSession, setStatus])

  async function speak(text: string, purpose: 'question' | 'feedback') { speechPurpose.current = purpose; await voice.speak(text) }
  async function startInterview() { setError(''); setStatus('starting'); try { const next = await interviewApi.start('Technical interview'); setSession(next); void speak(next.question, 'question') } catch (cause) { setStatus('error'); setError(cause instanceof ApiError ? cause.message : 'We couldn’t start the interview. Please try again.') } }
  function beginListening() { if (!session) return; setError(''); setSession({ ...session, transcript: '' }); void voice.start() }
  async function submitAnswer(text: string) { const active = sessionRef.current; if (!active || !text.trim()) { setError('Say a little more before submitting your answer.'); return } setError(''); setStatus('processing'); try { const result = await interviewApi.submitAnswer(active.id, text); setSession(result.session); const feedback = result.feedback.summary || 'Your answer has been reviewed.'; void speak(feedback, 'feedback') } catch (cause) { setStatus('error'); setError(cause instanceof ApiError ? cause.message : 'Your answer could not be sent. Please try again.') } }
  submitAnswerRef.current = submitAnswer
  async function nextQuestion() { if (!session) return; setStatus('processing'); try { if (session.questionNumber >= session.totalQuestions) { const completed = await interviewApi.complete(session.id); setSession(completed); setStatus('completed'); return } const next = await interviewApi.nextQuestion(session.id); setSession(next); void speak(next.question, 'question') } catch (cause) { setStatus('error'); setError(cause instanceof ApiError ? cause.message : 'We couldn’t load the next question.') } }
  const pct = session ? Math.round((session.questionNumber / session.totalQuestions) * 100) : 0
  return <main><nav><a className="brand"><span>V</span> VoxMock</a><div className="topic"><i /> {session?.topic ?? 'Voice technical interview'}</div><button className="exit" onClick={() => { voice.interrupt(); setSession(null); setStatus('idle') }}>Exit session</button></nav>
    <section className="hero"><div className="eyebrow"><Icon name="spark" /> AI TECHNICAL INTERVIEWER</div><h1>Speak your way to<br/><em>your next role.</em></h1><p>Practice high-signal technical interviews that listen, adapt, and help you improve in real time.</p>{!session && <button className="start" onClick={startInterview} disabled={status === 'starting'}>{status === 'starting' ? 'Starting…' : 'Start interview'} <Icon name="arrow" /></button>}</section>
    {session && <section className="workspace"><div className="question-card"><div className="q-meta"><span>QUESTION {session.questionNumber} OF {session.totalQuestions}</span><span className="adaptive">✦ Adaptive</span></div><h2>{session.question}</h2><div className="progress"><span style={{ width: `${pct}%` }} /></div><small>{pct}% complete</small></div>
      <div className="voice-stage"><div className={`orb ${status}`}><div className="orb-core"><Icon name="mic" /></div></div><div className="voice-state"><strong>{statusLabel[status]}</strong><span>{status === 'listening' ? 'Tap again when you’re done speaking' : status === 'speaking' ? 'Tap to interrupt and answer immediately' : 'Your response is captured live'}</span></div><div className="voice-actions">{status === 'listening' ? <button className="record stop" onClick={() => voice.stop()}>Finish answer</button> : <button className="record" onClick={beginListening} disabled={status === 'processing' || status === 'feedback' || status === 'completed'}><Icon name="mic" /> {voice.supported ? status === 'speaking' ? 'Interrupt & answer' : 'Tap to answer' : 'Voice unsupported'}</button>}{status === 'processing' && <span className="dots">•••</span>}{status === 'feedback' && <button className="record" onClick={nextQuestion}>Next question <Icon name="arrow" /></button>}</div></div>
      <aside className="insights"><h3>Live interview notes</h3>{session.transcript ? <div className="transcript"><label>LIVE TRANSCRIPT</label><p>“{session.transcript}”</p></div> : <div className="empty"><Icon name="sound" /><p>Your spoken answer will appear here.</p></div>}{session.feedback && <div className="feedback"><div className="score"><b>{session.feedback.score}</b><span>/100<br/>answer score</span></div><p>{session.feedback.summary}</p><div className="chips"><section><label>STRENGTHS</label>{session.feedback.strengths.map(x => <span key={x}>+ {x}</span>)}</section><section><label>GROW</label>{session.feedback.weaknesses.map(x => <span key={x}>→ {x}</span>)}</section></div>{session.feedback.relevantConcept && <div className="context">Relevant concept: <b>{session.feedback.relevantConcept}</b></div>}</div>}</aside></section>}
    {(error || status === 'error') && <div className="error" role="alert">{error}<button onClick={() => { setError(''); setStatus(session ? 'idle' : 'idle') }}>Dismiss</button></div>}
    {status === 'completed' && <div className="complete"><Icon name="spark" /><h2>Strong finish.</h2><p>Your session is complete.</p></div>}
  </main>
}
