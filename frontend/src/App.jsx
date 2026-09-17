import React, { useState, useEffect } from 'react'
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Workspace from './pages/Workspace.jsx'
import History from './pages/History.jsx'
import Review from './pages/Review.jsx'
import Sidebar from './components/Sidebar.jsx'

function Shell({ user, onLogout, children }) {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg">
      <Sidebar onLogout={onLogout} />
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  )
}

export default function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = localStorage.getItem('codelens_user')
    if (stored) setUser(JSON.parse(stored))
    setLoading(false)
  }, [])

  const handleLogin = (u) => {
    localStorage.setItem('codelens_user', JSON.stringify(u))
    setUser(u)
  }

  const handleLogout = () => {
    localStorage.removeItem('codelens_user')
    setUser(null)
  }

  if (loading) return null

  return (
    <HashRouter>
      <Routes>
        <Route
          path="/login"
          element={user ? <Navigate to="/" /> : <Login onLogin={handleLogin} />}
        />
        <Route
          path="/*"
          element={
            user ? (
              <Shell user={user} onLogout={handleLogout}>
                <Routes>
                  <Route path="/" element={<Dashboard user={user} />} />
                  <Route path="/language/:lang" element={<Workspace user={user} />} />
                  <Route path="/history" element={<History user={user} />} />
                  <Route path="/review" element={<Review user={user} />} />
                  <Route path="*" element={<Navigate to="/" />} />
                </Routes>
              </Shell>
            ) : (
              <Navigate to="/login" />
            )
          }
        />
      </Routes>
    </HashRouter>
  )
}
