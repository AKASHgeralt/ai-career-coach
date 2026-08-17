import API from './client'

export const getSummary = async () => {
  const res = await API.get('/api/analytics/summary')
  return res.data
}

export const getReadiness = async () => {
  const res = await API.get('/api/analytics/readiness')
  return res.data
}
export const getTimeline = async (limit = 40) => {
  const res = await API.get('/api/analytics/timeline', { params: { limit } })
  return res.data
}
