import { createContext, useState, useCallback, useEffect, ReactNode } from 'react'
import { authApi } from '../api/auth'

interface AuthContextValue {
  token: string
  currentUserId: number | null
  isLoggedIn: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

function parseJwt(token: string): { sub: string } | null {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload.replace(/-/g, '+').replace(/_/g, '/'))) as { sub: string }
  } catch {
    return null
  }
}

function loadToken(): string {
  const raw = localStorage.getItem('token') ?? ''
  // JWTは3つのドット区切りセグメントを持つ。それ以外は無効なトークンとして捨てる
  if (raw && raw.split('.').length !== 3) {
    localStorage.removeItem('token')
    return ''
  }
  return raw
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string>(loadToken)

  const currentUserId: number | null = token
    ? Number(parseJwt(token)?.sub ?? null)
    : null

  const login = useCallback(async (email: string, password: string) => {
    const accessToken = await authApi.login(email, password)
    localStorage.setItem('token', accessToken)
    setToken(accessToken)
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    await authApi.register(email, password)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setToken('')
  }, [])

  // axios interceptorが401を検知したときにReact状態も同期する
  useEffect(() => {
    const handler = () => setToken('')
    window.addEventListener('auth:logout', handler)
    return () => window.removeEventListener('auth:logout', handler)
  }, [])

  return (
    <AuthContext.Provider value={{ token, currentUserId, isLoggedIn: !!token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
