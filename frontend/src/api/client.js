import axios from 'axios'

// Empty string means "same origin", which is how the container setup works:
// nginx serves the app and proxies /api and /uploads to the backend, so no
// request is cross-origin. In local development the Vite server and the API
// are on different ports, hence the default.
export const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export const avatarSrc = (avatarUrl) => avatarUrl ? `${API_BASE_URL}${avatarUrl}` : null

const API = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Automatically attach JWT token to every request
API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto logout if token expires
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default API