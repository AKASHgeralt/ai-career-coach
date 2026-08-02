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