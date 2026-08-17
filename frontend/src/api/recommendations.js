import API from './client'

export const generateRoadmap = async (gapId, targetRole) => {
  const res = await API.post('/api/recommendations/roadmap', {
    gap_id: gapId,
    target_role: targetRole
  })
  return res.data
}

export const getRecommendation = async (gapId) => {
  const res = await API.get(`/api/recommendations/${gapId}`)
  return res.data
}

export const getRoadmapTasks = async (gapId) => {
  const res = await API.get(`/api/recommendations/${gapId}/tasks`)
  return res.data
}

export const setTaskCompleted = async (taskId, completed) => {
  const res = await API.patch(`/api/recommendations/tasks/${taskId}`, { completed })
  return res.data
}
