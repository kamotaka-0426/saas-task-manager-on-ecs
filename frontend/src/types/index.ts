export interface User {
  id: number
  email: string
}

export type Role = 'owner' | 'admin' | 'member'

export interface Organization {
  id: number
  name: string
  slug: string
  created_at: string
}

export interface Member {
  id: number
  user_id: number
  role: Role
}

export interface Project {
  id: number
  org_id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
}

export type Status = 'backlog' | 'todo' | 'in_progress' | 'done' | 'cancelled'
export type Priority = 'none' | 'low' | 'medium' | 'high' | 'urgent'
export type SortOption =
  | '-updated_at' | 'updated_at'
  | '-created_at' | 'created_at'
  | '-priority'   | 'priority'
  | '-status'     | 'status'

export interface UserMini {
  id: number
  email: string
}

export interface Label {
  id: number
  org_id: number
  name: string
  color: string
}

export interface Comment {
  id: number
  issue_id: number
  created_by: number
  content: string
  created_at: string
  updated_at: string
}

export interface ActivityLog {
  id: number
  issue_id: number
  user_id: number
  action: string
  field: string | null
  old_value: string | null
  new_value: string | null
  created_at: string
}

export interface Issue {
  id: number
  project_id: number
  title: string
  description: string | null
  status: Status
  priority: Priority
  created_by: number
  created_at: string
  updated_at: string
  assignees: UserMini[]
  labels: Label[]
}

export interface IssueDetail extends Issue {
  comments: Comment[]
  activity_logs: ActivityLog[]
}

export interface PaginatedIssues {
  items: Issue[]
  next_cursor: string | null
  total: number
}

export interface IssueCreate {
  title: string
  description?: string
  status?: Status
  priority?: Priority
}

export interface IssueUpdate {
  title?: string
  description?: string
  status?: Status
  priority?: Priority
}

export interface IssueListParams {
  status?: Status
  priority?: Priority
  assignee_id?: number
  label_id?: number
  q?: string
  sort?: SortOption
  cursor?: string
  limit?: number
}

export interface ProjectCreate {
  name: string
  description?: string
}

export interface LabelCreate {
  name: string
  color: string
}
