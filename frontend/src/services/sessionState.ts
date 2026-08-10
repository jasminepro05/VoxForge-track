import { useState } from 'react'
import type { InterviewSession } from './interviewApi'

export type InterviewStatus = 'idle' | 'starting' | 'listening' | 'processing' | 'speaking' | 'feedback' | 'error' | 'completed'

export function useSessionState() {
  const [status, setStatus] = useState<InterviewStatus>('idle')
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [error, setError] = useState('')
  return { status, setStatus, session, setSession, error, setError }
}
