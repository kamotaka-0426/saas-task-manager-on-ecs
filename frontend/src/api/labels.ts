import { client } from './client'
import type { Label, LabelCreate } from '../types'

const base = (orgId: number) => `/orgs/${orgId}/labels`

export const labelsApi = {
  list: async (orgId: number): Promise<Label[]> => {
    const { data } = await client.get<Label[]>(`${base(orgId)}/`)
    return data
  },

  create: async (orgId: number, body: LabelCreate): Promise<Label> => {
    const { data } = await client.post<Label>(`${base(orgId)}/`, body)
    return data
  },

  delete: async (orgId: number, labelId: number): Promise<void> => {
    await client.delete(`${base(orgId)}/${labelId}`)
  },
}
