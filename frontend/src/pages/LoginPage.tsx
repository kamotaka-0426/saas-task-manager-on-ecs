import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getApiErrorDetail } from '../lib/api'

export function LoginPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const [isRegistering, setIsRegistering] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isRegistering) {
        await register(email, password)
        setIsRegistering(false)
        setPassword('')
        setError('')
      } else {
        await login(email, password)
        navigate('/')
      }
    } catch (err: unknown) {
      const fallback = err instanceof Error ? err.message : 'An error occurred'
      setError(getApiErrorDetail(err, fallback))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="card auth-card">
        <h1 className="auth-title">Task Manager</h1>
        <p className="auth-subtitle">Multi-tenant task management</p>

        <h2 className="section-title">{isRegistering ? 'Create account' : 'Sign in'}</h2>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit} className="form">
          <label className="form-label">
            Email
            <input
              className="input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoFocus
            />
          </label>
          <label className="form-label">
            Password
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete={isRegistering ? 'new-password' : 'current-password'}
              required
            />
          </label>
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Loading…' : isRegistering ? 'Create account' : 'Sign in'}
          </button>
        </form>

        <button
          className="btn btn-ghost toggle-link"
          onClick={() => {
            setIsRegistering(!isRegistering)
            setError('')
          }}
        >
          {isRegistering ? 'Already have an account? Sign in' : "Don't have an account? Sign up"}
        </button>
      </div>
    </div>
  )
}
