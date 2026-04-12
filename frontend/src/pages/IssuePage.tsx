import { useState, useEffect, FormEvent, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { orgsApi } from '../api/organizations'
import { projectsApi } from '../api/projects'
import { issuesApi } from '../api/issues'
import { useAuth } from '../hooks/useAuth'
import { ROLE_RANK, STATUS_COLOR, PRIORITY_COLOR, STATUSES, PRIORITIES } from '../lib/issue'
import { getApiErrorDetail } from '../lib/api'
import type {
  Project, Issue, Member, Role, Status, Priority, SortOption,
} from '../types'

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: '-updated_at', label: 'Updated (newest)' },
  { value: 'updated_at',  label: 'Updated (oldest)' },
  { value: '-created_at', label: 'Created (newest)' },
  { value: 'created_at',  label: 'Created (oldest)' },
  { value: '-priority',   label: 'Priority (high→low)' },
  { value: 'priority',    label: 'Priority (low→high)' },
]

export function IssuePage() {
  const { orgId, projectId } = useParams<{ orgId: string; projectId: string }>()
  const navigate = useNavigate()
  const { currentUserId } = useAuth()

  const [project, setProject] = useState<Project | null>(null)
  const [issues, setIssues]   = useState<Issue[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [total, setTotal]     = useState(0)
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [showForm, setShowForm] = useState(false)

  // Filters
  const [filterStatus, setFilterStatus]     = useState<Status | ''>('')
  const [filterPriority, setFilterPriority] = useState<Priority | ''>('')
  const [sort, setSort]                     = useState<SortOption>('-updated_at')
  const [searchQuery, setSearchQuery]       = useState('')
  const [searchInput, setSearchInput]       = useState('')

  // New issue form
  const [title, setTitle]           = useState('')
  const [description, setDescription] = useState('')
  const [issueStatus, setIssueStatus] = useState<Status>('backlog')
  const [issuePriority, setIssuePriority] = useState<Priority>('none')
  const [error, setError]           = useState('')

  const oId = Number(orgId)
  const pId = Number(projectId)

  const myRole: Role | null =
    members.find((m) => m.user_id === currentUserId)?.role ?? null
  const canManage = myRole !== null && ROLE_RANK[myRole] >= ROLE_RANK.admin
  const isOwner   = myRole === 'owner'

  const loadIssues = useCallback(
    async (cursor?: string) => {
      const result = await issuesApi.list(oId, pId, {
        status:   filterStatus   || undefined,
        priority: filterPriority || undefined,
        q:        searchQuery    || undefined,
        sort,
        cursor,
        limit: 20,
      })
      return result
    },
    [oId, pId, filterStatus, filterPriority, searchQuery, sort],
  )

  // Initial load + filter changes
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([
      projectsApi.get(oId, pId),
      orgsApi.listMembers(oId),
      loadIssues(),
    ])
      .then(([p, m, paged]) => {
        if (cancelled) return
        setProject(p)
        setMembers(m)
        setIssues(paged.items)
        setTotal(paged.total)
        setNextCursor(paged.next_cursor)
      })
      .catch(() => navigate(`/orgs/${oId}`))
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [oId, pId, navigate, loadIssues])

  const handleLoadMore = async () => {
    if (!nextCursor) return
    setLoadingMore(true)
    try {
      const paged = await loadIssues(nextCursor)
      setIssues((prev) => [...prev, ...paged.items])
      setNextCursor(paged.next_cursor)
    } finally {
      setLoadingMore(false)
    }
  }

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      await issuesApi.create(oId, pId, {
        title, description, status: issueStatus, priority: issuePriority,
      })
      // Re-fetch from top to respect sort
      const paged = await loadIssues()
      setIssues(paged.items)
      setTotal(paged.total)
      setNextCursor(paged.next_cursor)
      setTitle('')
      setDescription('')
      setIssueStatus('backlog')
      setIssuePriority('none')
      setShowForm(false)
    } catch (err: unknown) {
      setError(getApiErrorDetail(err, 'Failed to create issue'))
    }
  }

  const handleDelete = async (issueId: number) => {
    if (!confirm('Delete this issue?')) return
    try {
      await issuesApi.delete(oId, pId, issueId)
      setIssues((prev) => prev.filter((i) => i.id !== issueId))
      setTotal((t) => t - 1)
    } catch {
      alert('Delete failed')
    }
  }

  if (loading) return <div className="page"><p className="muted">Loading…</p></div>

  return (
    <div className="page">
      <div className="breadcrumb">
        <Link to="/">Organizations</Link>
        <span className="separator">›</span>
        <Link to={`/orgs/${oId}`}>Projects</Link>
        <span className="separator">›</span>
        <span>{project?.name}</span>
      </div>

      <div className="page-header">
        <h1 className="page-title">Issues <span className="muted" style={{ fontSize: 14 }}>({total})</span></h1>
        {canManage && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ New Issue'}
          </button>
        )}
      </div>

      {/* ── Filter bar ── */}
      <div className="filter-bar">
        <form
          className="search-form"
          onSubmit={(e) => { e.preventDefault(); setSearchQuery(searchInput) }}
        >
          <input
            className="input search-input"
            placeholder="Search issues…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          {searchInput && (
            <button
              type="button"
              className="search-clear"
              onClick={() => { setSearchInput(''); setSearchQuery('') }}
            >×</button>
          )}
        </form>

        <select
          className="input filter-select"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as Status | '')}
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>

        <select
          className="input filter-select"
          value={filterPriority}
          onChange={(e) => setFilterPriority(e.target.value as Priority | '')}
        >
          <option value="">All priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <select
          className="input filter-select"
          value={sort}
          onChange={(e) => setSort(e.target.value as SortOption)}
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* ── New issue form ── */}
      {showForm && (
        <div className="card form-card">
          <h2 className="section-title">Create Issue</h2>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleCreate} className="form">
            <label className="form-label">
              Title
              <input
                className="input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Fix the login bug"
                required
              />
            </label>
            <label className="form-label">
              Description
              <textarea
                className="input textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Steps to reproduce…"
              />
            </label>
            <div className="form-row">
              <label className="form-label">
                Status
                <select
                  className="input"
                  value={issueStatus}
                  onChange={(e) => setIssueStatus(e.target.value as Status)}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>{s.replace('_', ' ')}</option>
                  ))}
                </select>
              </label>
              <label className="form-label">
                Priority
                <select
                  className="input"
                  value={issuePriority}
                  onChange={(e) => setIssuePriority(e.target.value as Priority)}
                >
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>{p}</option>
                  ))}
                </select>
              </label>
            </div>
            <button className="btn btn-primary" type="submit">Create Issue</button>
          </form>
        </div>
      )}

      {/* ── Issue list ── */}
      {issues.length === 0 ? (
        <div className="empty-state">
          <p>No issues found.</p>
          {canManage && !filterStatus && !filterPriority && (
            <p className="muted">Create one to start tracking work.</p>
          )}
        </div>
      ) : (
        <>
          <div className="issue-list">
            {issues.map((issue) => (
              <div
                key={issue.id}
                className="card issue-card issue-card-link"
                onClick={() => navigate(`/orgs/${oId}/projects/${pId}/issues/${issue.id}`)}
              >
                <div className="issue-header">
                  <span className="issue-title">{issue.title}</span>
                  <div className="issue-actions" onClick={(e) => e.stopPropagation()}>
                    <span
                      className="badge"
                      style={{ color: STATUS_COLOR[issue.status] }}
                    >
                      {issue.status.replace('_', ' ')}
                    </span>
                    <span
                      className="badge priority-badge"
                      style={{ color: PRIORITY_COLOR[issue.priority] }}
                    >
                      {issue.priority}
                    </span>
                    {issue.labels.map((lb) => (
                      <span
                        key={lb.id}
                        className="label-chip"
                        style={{ background: lb.color + '33', color: lb.color, borderColor: lb.color + '66' }}
                      >
                        {lb.name}
                      </span>
                    ))}
                    {isOwner && (
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => handleDelete(issue.id)}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </div>
                {issue.description && (
                  <p className="issue-description muted">{issue.description}</p>
                )}
                {issue.assignees.length > 0 && (
                  <div className="assignee-row">
                    {issue.assignees.map((a) => (
                      <span key={a.id} className="assignee-chip">{a.email}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {nextCursor && (
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <button
                className="btn btn-ghost"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? 'Loading…' : 'Load more'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
