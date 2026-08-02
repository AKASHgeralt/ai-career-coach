import API from './client'

export const getSummary = async () => {
  const res = await API.get('/api/analytics/summary')
  return res.data
}