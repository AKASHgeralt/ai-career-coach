import API from './client'

export const register = async (full_name, email, password) => {
  const res = await API.post('/api/auth/register', { full_name, email, password })
  return res.data
}

export const login = async (email, password) => {
  const formData = new URLSearchParams()
  formData.append('username', email)
  formData.append('password', password)
  const res = await API.post('/api/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  return res.data
}

export const getMe = async () => {
  const res = await API.get('/api/users/me')
  return res.data
}

export const uploadAvatar = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  const res = await API.post('/api/users/me/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return res.data
}

export const removeAvatar = async () => {
  const res = await API.delete('/api/users/me/avatar')
  return res.data
}

export const getTargetRoles = async () => {
  const res = await API.get('/api/users/target-roles')
  return res.data
}

export const setTargetRole = async (slug) => {
  const res = await API.put('/api/users/me/target-role', { target_role: slug })
  return res.data
}