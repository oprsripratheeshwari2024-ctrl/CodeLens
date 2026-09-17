import React, { useState } from 'react'
import { Code2 } from 'lucide-react'
import api from '../services/api.js'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleContinue = async (e) => {
    e.preventDefault()
    if (!EMAIL_RE.test(email)) {
      setError('Please enter a valid email address.')
      return
    }
    setError('')
    setLoading(true)
    try {
      const res = await api.login(email)
      onLogin(res)
   } catch (err) {
  console.error('CodeLens login error:', err)
  setError(err.response?.data?.detail || err.message || 'Login failed')
} finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-bg">
      <div className="w-full max-w-sm px-6">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center shadow-glow mb-4">
            <Code2 className="text-white" size={28} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">CODELENS</h1>
          <p className="text-sm text-gray-400 mt-1">AI-Powered Code Analysis</p>
        </div>

        <form onSubmit={handleContinue} className="card p-6 space-y-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-surface2 border border-border rounded-lg px-3 py-2.5 text-sm outline-none focus:border-primary transition-colors"
              autoFocus
            />
          </div>
          {error && <p className="text-xs text-danger">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 text-sm disabled:opacity-60">
            {loading ? 'Continuing…' : 'Continue'}
          </button>
        </form>
        <p className="text-center text-xs text-gray-600 mt-6">
          No password, no OTP — just your email to get started.
        </p>
      </div>
    </div>
  )
}
