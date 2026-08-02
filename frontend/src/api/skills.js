import API from './client'

export const analyzeSkillGap = async (resumeId, jobTitle, jobDescription) => {
  const res = await API.post('/api/skills/analyze', {
    resume_id: resumeId,
    job_title: jobTitle,
    job_description: jobDescription
  })
  return res.data
}

export const getSkillGaps = async (resumeId) => {
  const res = await API.get(`/api/skills/gaps/${resumeId}`)
  return res.data
}