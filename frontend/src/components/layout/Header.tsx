import { Link } from 'react-router-dom'

interface HeaderProps {
  isLoggedIn: boolean
  onLogout: () => void
}

export function Header({ isLoggedIn, onLogout }: HeaderProps) {
  return (
    <header className="header">
      <Link to="/" className="header-logo">
        Task Manager
      </Link>
      {isLoggedIn && (
        <button className="btn btn-ghost" onClick={onLogout}>
          Logout
        </button>
      )}
    </header>
  )
}
