import { useState, useEffect, FormEvent } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { orgsApi } from '../api/organizations'
import { projectsApi } from '../api/projects'
import { ROLE_RANK } from '../lib/issue'
import { getApiErrorDetail } from '../lib/api'
import type { Organization, Project, Member, Role } from '../types'
import { useAuth } from '../hooks/useAuth'

export function ProjectPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const navigate = useNavigate()
  const { currentUserId } = useAuth()

  const [org, setOrg] = useState<Organization | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')

  const id = Number(orgId)

  const myRole: Role | null =
    members.find((m) => m.user_id === currentUserId)?.role ?? null
  const canManage = myRole !== null && ROLE_RANK[myRole] >= ROLE_RANK.admin

  useEffect(() => {
    Promise.all([orgsApi.get(id), projectsApi.list(id), orgsApi.listMembers(id)])
      .then(([o, p, m]) => {
        setOrg(o)
        setProjects(p)
        setMembers(m)
      })
      .catch(() => navigate('/'))
      .finally(() => setLoading(false))
  }, [id, navigate])

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      const project = await projectsApi.create(id, { name, description })
      setProjects((prev) => [...prev, project])
      setName('')
      setDescription('')
      setShowForm(false)
    } catch (err: unknown) {
      setError(getApiErrorDetail(err, 'Failed to create project'))
    }
  }

  const handleDelete = async (projectId: number) => {
    if (!confirm('Delete this project and all its issues?')) return
    try {
      await projectsApi.delete(id, projectId)
      setProjects((prev) => prev.filter((p) => p.id !== projectId))
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
        <span>{org?.name}</span>
      </div>

      <div className="page-header">
        <h1 className="page-title">Projects</h1>
        {canManage && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ New Project'}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card form-card">
          <h2 className="section-title">Create Project</h2>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleCreate} className="form">
            <label className="form-label">
              Name
              <input
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Project Alpha"
                required
              />
            </label>
            <label className="form-label">
              Description
              <textarea
                className="input textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What is this project about?"
              />
            </label>
            <button className="btn btn-primary" type="submit">
              Create
            </button>
          </form>
        </div>
      )}

      {projects.length === 0 ? (
        <div className="empty-state">
          <p>No projects yet.</p>
          {canManage && <p className="muted">Create one to start tracking issues.</p>}
        </div>
      ) : (
        <div className="grid">
          {projects.map((project) => (
            <div key={project.id} className="card card-row">
              <button
                className="card-clickable card-body"
                onClick={() => navigate(`/orgs/${id}/projects/${project.id}`)}
              >
                <h2 className="card-title">{project.name}</h2>
                {project.description && <p className="muted">{project.description}</p>}
              </button>
              {myRole === 'owner' && (
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(project.id)}
                >
                  Delete
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
