import { useState, useEffect, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { orgsApi } from '../api/organizations'
import type { Organization } from '../types'

export function DashboardPage() {
  const navigate = useNavigate()
  const [orgs, setOrgs] = useState<Organization[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    orgsApi.list().then(setOrgs).catch(console.error).finally(() => setLoading(false))
  }, [])

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    try {
      const org = await orgsApi.create(name, slug)
      setOrgs((prev) => [...prev, org])
      setName('')
      setSlug('')
      setShowForm(false)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } }).response?.data
        ?.detail
      setError(detail ?? 'Failed to create organization')
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Organizations</h1>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Organization'}
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h2 className="section-title">Create Organization</h2>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleCreate} className="form">
            <label className="form-label">
              Name
              <input
                className="input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Acme Corp"
                required
              />
            </label>
            <label className="form-label">
              Slug <span className="hint">(URL-safe identifier)</span>
              <input
                className="input"
                value={slug}
                onChange={(e) => setSlug(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
                placeholder="acme-corp"
                required
              />
            </label>
            <button className="btn btn-primary" type="submit">
              Create
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <p className="muted">Loading…</p>
      ) : orgs.length === 0 ? (
        <div className="empty-state">
          <p>No organizations yet.</p>
          <p className="muted">Create one to get started.</p>
        </div>
      ) : (
        <div className="grid">
          {orgs.map((org) => (
            <button
              key={org.id}
              className="card card-clickable"
              onClick={() => navigate(`/orgs/${org.id}`)}
            >
              <div className="card-body">
                <h2 className="card-title">{org.name}</h2>
                <p className="muted">{org.slug}</p>
              </div>
              <span className="arrow">›</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
