import { client } from './client'
import type {
  Issue, IssueCreate, IssueUpdate, IssueDetail,
  PaginatedIssues, IssueListParams, Comment, ActivityLog,
} from '../types'

const base = (orgId: number, projectId: number) =>
  `/orgs/${orgId}/projects/${projectId}/issues`

export const issuesApi = {
  list: async (
    orgId: number,
    projectId: number,
    params?: IssueListParams,
  ): Promise<PaginatedIssues> => {
    const { data } = await client.get<PaginatedIssues>(
      `${base(orgId, projectId)}/`,
      { params },
    )
    return data
  },

  get: async (orgId: number, projectId: number, issueId: number): Promise<IssueDetail> => {
    const { data } = await client.get<IssueDetail>(
      `${base(orgId, projectId)}/${issueId}`,
    )
    return data
  },

  create: async (orgId: number, projectId: number, body: IssueCreate): Promise<Issue> => {
    const { data } = await client.post<Issue>(`${base(orgId, projectId)}/`, body)
    return data
  },

  update: async (
    orgId: number,
    projectId: number,
    issueId: number,
    body: IssueUpdate,
  ): Promise<Issue> => {
    const { data } = await client.patch<Issue>(
      `${base(orgId, projectId)}/${issueId}`,
      body,
    )
    return data
  },

  delete: async (orgId: number, projectId: number, issueId: number): Promise<void> => {
    await client.delete(`${base(orgId, projectId)}/${issueId}`)
  },

  // ── Assignees ──────────────────────────────────────────────────────────────

  addAssignee: async (
    orgId: number,
    projectId: number,
    issueId: number,
    userId: number,
  ): Promise<IssueDetail> => {
    const { data } = await client.post<IssueDetail>(
      `${base(orgId, projectId)}/${issueId}/assignees/${userId}`,
    )
    return data
  },

  removeAssignee: async (
    orgId: number,
    projectId: number,
    issueId: number,
    userId: number,
  ): Promise<void> => {
    await client.delete(`${base(orgId, projectId)}/${issueId}/assignees/${userId}`)
  },

  // ── Labels ─────────────────────────────────────────────────────────────────

  addLabel: async (
    orgId: number,
    projectId: number,
    issueId: number,
    labelId: number,
  ): Promise<IssueDetail> => {
    const { data } = await client.post<IssueDetail>(
      `${base(orgId, projectId)}/${issueId}/labels/${labelId}`,
    )
    return data
  },

  removeLabel: async (
    orgId: number,
    projectId: number,
    issueId: number,
    labelId: number,
  ): Promise<void> => {
    await client.delete(`${base(orgId, projectId)}/${issueId}/labels/${labelId}`)
  },

  // ── Comments ───────────────────────────────────────────────────────────────

  listComments: async (
    orgId: number,
    projectId: number,
    issueId: number,
  ): Promise<Comment[]> => {
    const { data } = await client.get<Comment[]>(
      `${base(orgId, projectId)}/${issueId}/comments`,
    )
    return data
  },

  addComment: async (
    orgId: number,
    projectId: number,
    issueId: number,
    content: string,
  ): Promise<Comment> => {
    const { data } = await client.post<Comment>(
      `${base(orgId, projectId)}/${issueId}/comments`,
      { content },
    )
    return data
  },

  deleteComment: async (
    orgId: number,
    projectId: number,
    issueId: number,
    commentId: number,
  ): Promise<void> => {
    await client.delete(`${base(orgId, projectId)}/${issueId}/comments/${commentId}`)
  },

  // ── Activity ───────────────────────────────────────────────────────────────

  listActivity: async (
    orgId: number,
    projectId: number,
    issueId: number,
  ): Promise<ActivityLog[]> => {
    const { data } = await client.get<ActivityLog[]>(
      `${base(orgId, projectId)}/${issueId}/activity`,
    )
    return data
  },
}
