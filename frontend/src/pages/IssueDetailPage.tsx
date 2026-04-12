import { useState, useEffect, FormEvent } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { orgsApi } from '../api/organizations'
import { issuesApi } from '../api/issues'
import { labelsApi } from '../api/labels'
import { useAuth } from '../hooks/useAuth'
import { ROLE_RANK, STATUS_COLOR, PRIORITY_COLOR, STATUSES, PRIORITIES, formatDate } from '../lib/issue'
import { getApiErrorDetail } from '../lib/api'
import type {
  IssueDetail, Member, Label, Role, Status, Priority,
} from '../types'

export function IssueDetailPage() {
  const { orgId, projectId, issueId } = useParams<{
    orgId: string; projectId: string; issueId: string
  }>()
  const navigate = useNavigate()
  const { currentUserId } = useAuth()

  const [issue, setIssue]     = useState<IssueDetail | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [orgLabels, setOrgLabels] = useState<Label[]>([])
  const [loading, setLoading] = useState(true)

  // Comment form
  const [commentText, setCommentText] = useState('')
  const [commentError, setCommentError] = useState('')
  const [submittingComment, setSubmittingComment] = useState(false)

  const oId  = Number(orgId)
  const pId  = Number(projectId)
  const iId  = Number(issueId)

  const myRole: Role | null =
    members.find((m) => m.user_id === currentUserId)?.role ?? null
  const canManage = myRole !== null && ROLE_RANK[myRole] >= ROLE_RANK.admin

  const reload = async () => {
    const updated = await issuesApi.get(oId, pId, iId)
    setIssue(updated)
  }

  useEffect(() => {
    setLoading(true)
    Promise.all([
      issuesApi.get(oId, pId, iId),
      orgsApi.listMembers(oId),
      labelsApi.list(oId),
    ])
      .then(([iss, mem, lbs]) => {
        setIssue(iss)
        setMembers(mem)
        setOrgLabels(lbs)
      })
      .catch(() => navigate(`/orgs/${oId}/projects/${pId}`))
      .finally(() => setLoading(false))
  }, [oId, pId, iId, navigate])

  // ── Status / Priority change ─────────────────────────────────────────────

  const handleStatusChange = async (newStatus: Status) => {
    if (!issue) return
    try {
      await issuesApi.update(oId, pId, iId, { status: newStatus })
      await reload()
    } catch { alert('Update failed') }
  }

  const handlePriorityChange = async (newPriority: Priority) => {
    if (!issue) return
    try {
      await issuesApi.update(oId, pId, iId, { priority: newPriority })
      await reload()
    } catch { alert('Update failed') }
  }

  // ── Assignees ────────────────────────────────────────────────────────────

  const handleAddAssignee = async (userId: number) => {
    try {
      await issuesApi.addAssignee(oId, pId, iId, userId)
      await reload()
    } catch { alert('Failed to add assignee') }
  }

  const handleRemoveAssignee = async (userId: number) => {
    try {
      await issuesApi.removeAssignee(oId, pId, iId, userId)
      await reload()
    } catch { alert('Failed to remove assignee') }
  }

  // ── Labels ───────────────────────────────────────────────────────────────

  const handleAddLabel = async (labelId: number) => {
    try {
      await issuesApi.addLabel(oId, pId, iId, labelId)
      await reload()
    } catch { alert('Failed to add label') }
  }

  const handleRemoveLabel = async (labelId: number) => {
    try {
      await issuesApi.removeLabel(oId, pId, iId, labelId)
      await reload()
    } catch { alert('Failed to remove label') }
  }

  // ── Comments ─────────────────────────────────────────────────────────────

  const handleAddComment = async (e: FormEvent) => {
    e.preventDefault()
    if (!commentText.trim()) return
    setCommentError('')
    setSubmittingComment(true)
    try {
      await issuesApi.addComment(oId, pId, iId, commentText.trim())
      setCommentText('')
      await reload()
    } catch (err: unknown) {
      setCommentError(getApiErrorDetail(err, 'Failed to post comment'))
    } finally {
      setSubmittingComment(false)
    }
  }

  const handleDeleteComment = async (commentId: number) => {
    if (!confirm('Delete this comment?')) return
    try {
      await issuesApi.deleteComment(oId, pId, iId, commentId)
      await reload()
    } catch { alert('Delete failed') }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  if (loading || !issue) return <div className="page"><p className="muted">Loading…</p></div>

  const assignedIds = new Set(issue.assignees.map((a) => a.id))
  const attachedLabelIds = new Set(issue.labels.map((l) => l.id))

  const availableAssignees = members.filter((m) => !assignedIds.has(m.user_id))
  const availableLabels    = orgLabels.filter((l) => !attachedLabelIds.has(l.id))

  return (
    <div className="page page-wide">
      <div className="breadcrumb">
        <Link to="/">Organizations</Link>
        <span className="separator">›</span>
        <Link to={`/orgs/${oId}`}>Projects</Link>
        <span className="separator">›</span>
        <Link to={`/orgs/${oId}/projects/${pId}`}>Issues</Link>
        <span className="separator">›</span>
        <span>#{issue.id}</span>
      </div>

      {/* ── Issue header ── */}
      <div className="issue-detail-header">
        <h1 className="issue-detail-title">{issue.title}</h1>
        <div className="issue-detail-meta">
          {canManage ? (
            <select
              className="input badge-select-lg"
              style={{ color: STATUS_COLOR[issue.status] }}
              value={issue.status}
              onChange={(e) => handleStatusChange(e.target.value as Status)}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s.replace('_', ' ')}</option>
              ))}
            </select>
          ) : (
            <span className="badge-lg" style={{ color: STATUS_COLOR[issue.status] }}>
              {issue.status.replace('_', ' ')}
            </span>
          )}

          {canManage ? (
            <select
              className="input badge-select-lg"
              style={{ color: PRIORITY_COLOR[issue.priority] }}
              value={issue.priority}
              onChange={(e) => handlePriorityChange(e.target.value as Priority)}
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          ) : (
            <span className="badge-lg" style={{ color: PRIORITY_COLOR[issue.priority] }}>
              {issue.priority}
            </span>
          )}
        </div>
      </div>

      {issue.description && (
        <div className="card detail-section">
          <p style={{ whiteSpace: 'pre-wrap' }}>{issue.description}</p>
        </div>
      )}

      <div className="detail-layout">
        {/* ── Main column ── */}
        <div className="detail-main">

          {/* Comments */}
          <div className="card detail-section">
            <h2 className="section-title">
              Comments <span className="muted hint">({issue.comments.length})</span>
            </h2>
            {issue.comments.length === 0 && (
              <p className="muted">No comments yet.</p>
            )}
            <div className="comment-list">
              {issue.comments.map((c) => (
                <div key={c.id} className="comment">
                  <div className="comment-header">
                    <span className="comment-author muted">{c.created_by}</span>
                    <span className="comment-date muted">{formatDate(c.created_at)}</span>
                    {c.created_by === currentUserId && (
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleDeleteComment(c.id)}
                        style={{ marginLeft: 'auto', color: 'var(--danger)' }}
                      >
                        Delete
                      </button>
                    )}
                  </div>
                  <p className="comment-body">{c.content}</p>
                </div>
              ))}
            </div>

            {canManage && (
              <form onSubmit={handleAddComment} className="comment-form">
                {commentError && <div className="alert alert-error">{commentError}</div>}
                <textarea
                  className="input textarea"
                  placeholder="Leave a comment…"
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  rows={3}
                />
                <button
                  className="btn btn-primary"
                  type="submit"
                  disabled={submittingComment || !commentText.trim()}
                >
                  {submittingComment ? 'Posting…' : 'Comment'}
                </button>
              </form>
            )}
          </div>

          {/* Activity log */}
          <div className="card detail-section">
            <h2 className="section-title">Activity</h2>
            {issue.activity_logs.length === 0 && (
              <p className="muted">No activity yet.</p>
            )}
            <ul className="activity-list">
              {issue.activity_logs.map((log) => (
                <li key={log.id} className="activity-item">
                  <span className="activity-dot" />
                  <span className="activity-body">
                    <span className="muted">User #{log.user_id}</span>{' '}
                    <strong>{log.action.replace('_', ' ')}</strong>
                    {log.field && (
                      <span className="muted">
                        {' '}({log.old_value ?? '—'} → {log.new_value ?? '—'})
                      </span>
                    )}
                  </span>
                  <span className="activity-time muted">{formatDate(log.created_at)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* ── Sidebar ── */}
        <aside className="detail-sidebar">

          {/* Assignees */}
          <div className="card detail-section">
            <h2 className="section-title sidebar-section-title">Assignees</h2>
            {issue.assignees.length === 0 && (
              <p className="muted" style={{ marginBottom: 8 }}>None</p>
            )}
            <div className="sidebar-chips">
              {issue.assignees.map((a) => (
                <div key={a.id} className="sidebar-chip">
                  <span>{a.email}</span>
                  {canManage && (
                    <button
                      className="chip-remove"
                      onClick={() => handleRemoveAssignee(a.id)}
                    >×</button>
                  )}
                </div>
              ))}
            </div>
            {canManage && availableAssignees.length > 0 && (
              <select
                className="input"
                style={{ marginTop: 8 }}
                value=""
                onChange={(e) => handleAddAssignee(Number(e.target.value))}
              >
                <option value="">+ Assign member</option>
                {availableAssignees.map((m) => (
                  <option key={m.user_id} value={m.user_id}>
                    User #{m.user_id} ({m.role})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Labels */}
          <div className="card detail-section">
            <h2 className="section-title sidebar-section-title">Labels</h2>
            {issue.labels.length === 0 && (
              <p className="muted" style={{ marginBottom: 8 }}>None</p>
            )}
            <div className="sidebar-chips">
              {issue.labels.map((lb) => (
                <div key={lb.id} className="sidebar-chip">
                  <span
                    className="label-chip"
                    style={{
                      background: lb.color + '33',
                      color: lb.color,
                      borderColor: lb.color + '66',
                    }}
                  >
                    {lb.name}
                  </span>
                  {canManage && (
                    <button
                      className="chip-remove"
                      onClick={() => handleRemoveLabel(lb.id)}
                    >×</button>
                  )}
                </div>
              ))}
            </div>
            {canManage && availableLabels.length > 0 && (
              <select
                className="input"
                style={{ marginTop: 8 }}
                value=""
                onChange={(e) => handleAddLabel(Number(e.target.value))}
              >
                <option value="">+ Add label</option>
                {availableLabels.map((lb) => (
                  <option key={lb.id} value={lb.id}>{lb.name}</option>
                ))}
              </select>
            )}
            {canManage && orgLabels.length === 0 && (
              <p className="muted hint" style={{ marginTop: 4 }}>
                No labels in this org yet.
              </p>
            )}
          </div>

          {/* Meta */}
          <div className="card detail-section meta-section">
            <div className="meta-row">
              <span className="muted">Created</span>
              <span>{formatDate(issue.created_at)}</span>
            </div>
            <div className="meta-row">
              <span className="muted">Updated</span>
              <span>{formatDate(issue.updated_at)}</span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}
