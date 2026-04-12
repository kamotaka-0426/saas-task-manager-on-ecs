import type { Role, Status, Priority } from '../types'

export const ROLE_RANK: Record<Role, number> = { member: 0, admin: 1, owner: 2 }

export const STATUS_COLOR: Record<Status, string> = {
  backlog:     '#666',
  todo:        '#4a90e2',
  in_progress: '#f5a623',
  done:        '#4caf50',
  cancelled:   '#e74c3c',
}

export const PRIORITY_COLOR: Record<Priority, string> = {
  none:   '#555',
  low:    '#4a90e2',
  medium: '#f5a623',
  high:   '#e74c3c',
  urgent: '#9b59b6',
}

export const STATUSES: Status[]   = ['backlog', 'todo', 'in_progress', 'done', 'cancelled']
export const PRIORITIES: Priority[] = ['none', 'low', 'medium', 'high', 'urgent']

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
