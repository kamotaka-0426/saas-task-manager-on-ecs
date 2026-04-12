import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { Header } from './components/layout/Header'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { ProjectPage } from './pages/ProjectPage'
import { IssuePage } from './pages/IssuePage'
import { IssueDetailPage } from './pages/IssueDetailPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isLoggedIn } = useAuth()
  return isLoggedIn ? <>{children}</> : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { isLoggedIn, logout } = useAuth()
  return (
    <>
      <Header isLoggedIn={isLoggedIn} onLogout={logout} />
      <main className="main">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <DashboardPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/orgs/:orgId"
            element={
              <PrivateRoute>
                <ProjectPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/orgs/:orgId/projects/:projectId"
            element={
              <PrivateRoute>
                <IssuePage />
              </PrivateRoute>
            }
          />
          <Route
            path="/orgs/:orgId/projects/:projectId/issues/:issueId"
            element={
              <PrivateRoute>
                <IssueDetailPage />
              </PrivateRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
