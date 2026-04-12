import { client } from './client'
import type { Organization, Member } from '../types'

export const orgsApi = {
  list: async (): Promise<Organization[]> => {
    const { data } = await client.get<Organization[]>('/orgs/')
    return data
  },

  create: async (name: string, slug: string): Promise<Organization> => {
    const { data } = await client.post<Organization>('/orgs/', { name, slug })
    return data
  },

  get: async (orgId: number): Promise<Organization> => {
    const { data } = await client.get<Organization>(`/orgs/${orgId}`)
    return data
  },

  listMembers: async (orgId: number): Promise<Member[]> => {
    const { data } = await client.get<Member[]>(`/orgs/${orgId}/members`)
    return data
  },
}
