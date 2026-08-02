import API from './client'

export const startInterview = async (jobRole, difficulty) => {
  const res = await API.post('/api/interview/start', {
    job_role: jobRole,
    difficulty: difficulty
  })
  return res.data
}

export const submitAnswer = async (sessionId, answer) => {
  const res = await API.post('/api/interview/answer', {
    session_id: sessionId,
    answer: answer
  })
  return res.data
}

export const getSessions = async () => {
  const res = await API.get('/api/interview/sessions')
  return res.data
}