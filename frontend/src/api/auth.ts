import { client } from './client'
import type { User } from '../types'

export const authApi = {
  register: async (email: string, password: string): Promise<User> => {
    const { data } = await client.post<User>('/auth/register', { email, password })
    return data
  },

  login: async (email: string, password: string): Promise<string> => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    const { data } = await client.post<{ access_token: string }>('/auth/login', form)
    return data.access_token
  },
}
