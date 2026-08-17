import API from './client'

export const uploadResume = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const res = await API.post('/api/resumes/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export const getResumes = async () => {
  const res = await API.get('/api/resumes')
  return res.data
}

export const analyzeResume = async (resumeId) => {
  const res = await API.get(`/api/resumes/${resumeId}/analyze`)
  return res.data
}

export const deleteResume = async (resumeId) => {
  const res = await API.delete(`/api/resumes/${resumeId}`)
  return res.data
}
export const getVersionHistory = async () => {
  const res = await API.get('/api/resumes/versions')
  return res.data
}

export const compareVersions = async (base, target) => {
  const res = await API.get('/api/resumes/compare', { params: { base, target } })
  return res.data
}
