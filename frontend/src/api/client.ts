import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL as string | undefined ?? 'http://localhost:8000'

export const client = axios.create({ baseURL: API_URL })

// Attach JWT token to every request
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401, clear token (caller decides whether to redirect)
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) localStorage.removeItem('token')
    return Promise.reject(err)
  },
)
