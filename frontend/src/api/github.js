import API from './client'

export const connectGithub = async (username, force = false) => {
  const res = await API.post('/api/github/connect', {
    github_username: username,
    force,
  })
  return res.data
}

export const getGithubProfile = async () => {
  const res = await API.get('/api/github/profile')
  return res.data
}