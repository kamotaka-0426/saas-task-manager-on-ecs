import { client } from './client'
import type { Project, ProjectCreate } from '../types'

export const projectsApi = {
  list: async (orgId: number): Promise<Project[]> => {
    const { data } = await client.get<Project[]>(`/orgs/${orgId}/projects/`)
    return data
  },

  create: async (orgId: number, body: ProjectCreate): Promise<Project> => {
    const { data } = await client.post<Project>(`/orgs/${orgId}/projects/`, body)
    return data
  },

  get: async (orgId: number, projectId: number): Promise<Project> => {
    const { data } = await client.get<Project>(`/orgs/${orgId}/projects/${projectId}`)
    return data
  },

  update: async (
    orgId: number,
    projectId: number,
    body: Partial<ProjectCreate>,
  ): Promise<Project> => {
    const { data } = await client.patch<Project>(
      `/orgs/${orgId}/projects/${projectId}`,
      body,
    )
    return data
  },

  delete: async (orgId: number, projectId: number): Promise<void> => {
    await client.delete(`/orgs/${orgId}/projects/${projectId}`)
  },
}
