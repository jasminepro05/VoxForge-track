const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {}

export interface Feedback { score: number; correctness: string; summary: string; strengths: string[]; weaknesses: string[]; missingConcepts: string[]; relevantConcept?: string }
export interface InterviewSession { id: string; userId: string; topic: string; question: string; questionNumber: number; totalQuestions: number; transcript: string; feedback: Feedback | null; completed: boolean }

function camelizeSession(value: any): InterviewSession {
  const feedback = value.feedback && { ...value.feedback, missingConcepts: value.feedback.missing_concepts ?? [], relevantConcept: value.feedback.relevant_concept }
  return { ...value, userId: value.user_id, questionNumber: value.question_number, totalQuestions: value.total_questions, feedback }
}

async function request(path: string, init?: RequestInit): Promise<any> {
  let response: Response
  try { response = await fetch(`${BASE_URL}${path}`, init) } catch { throw new ApiError('Could not reach the interview server.') }
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new ApiError(body.detail ?? 'The interview request failed.') }
  return response.json()
}

export const interviewApi = {
  async start(topic: string) { return camelizeSession(await request('/api/interview/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic }) })) },
  async submitAnswer(id: string, transcript: string) { const payload = await request(`/api/interview/${id}/answer`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ transcript }) }); return { session: camelizeSession(payload.session), feedback: { ...payload.feedback, missingConcepts: payload.feedback.missing_concepts ?? [], relevantConcept: payload.feedback.relevant_concept } as Feedback } },
  async nextQuestion(id: string) { return camelizeSession(await request(`/api/interview/${id}/next`, { method: 'POST' })) },
  async complete(id: string) { return camelizeSession(await request(`/api/interview/${id}/end`, { method: 'POST' })) },
}
