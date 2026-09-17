import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart3, Gauge, Clock } from 'lucide-react'
import api from '../services/api.js'

const CARD_DEFS = [
  { key: 'total_analyses', label: 'Total Analyses' },
  { key: 'python_analyses', label: 'Python Analyses' },
  { key: 'java_analyses', label: 'Java Analyses' },
  { key: 'cpp_analyses', label: 'C++ Analyses' },
  { key: 'c_analyses', label: 'C Analyses' },
  { key: 'average_quality', label: 'Average Code Quality', suffix: '/100' },
]

export default function Dashboard({ user }) {
  const [stats, setStats] = useState(null)
  const [recent, setRecent] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.dashboard(user.user_id)
      .then((d) => { setStats(d.stats); setRecent(d.recent) })
      .catch(() => setError('Could not reach the CodeLens backend.'))
  }, [user.user_id])

  return (
    <div className="p-8 max-w-6xl mx-auto fade-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white tracking-tight">CODELENS</h1>
        <p className="text-gray-400 mt-1">Welcome back, {user.email}!</p>
        <p className="text-sm text-primary-light mt-0.5">Analyze • Understand • Fix • Visualize</p>
      </div>

      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-10">
        {CARD_DEFS.map((c) => (
          <div key={c.key} className="card card-glow p-5">
            <div className="flex items-center gap-2 text-gray-400 text-xs mb-2">
              <Gauge size={14} />
              {c.label}
            </div>
            <div className="text-3xl font-bold text-white">
              {stats ? stats[c.key] : '—'}
              {c.suffix && stats ? <span className="text-base text-gray-500">{c.suffix}</span> : null}
            </div>
          </div>
        ))}
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-2 text-white font-semibold mb-4">
          <Clock size={16} className="text-primary" />
          Recent Analysis History
        </div>
        {recent.length === 0 ? (
          <p className="text-sm text-gray-500">
            No analyses yet — pick a language from the sidebar to get started.
          </p>
        ) : (
          <div className="space-y-2">
            {recent.map((r) => (
              <div key={r.id} className="flex items-center justify-between py-2 px-3 rounded-lg bg-surface2 border border-border">
                <div>
                  <span className="text-sm text-white font-medium capitalize">{r.language}</span>
                  <p className="text-xs text-gray-500 truncate max-w-md">{r.summary}</p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-primary-light font-semibold">{r.quality_score}/100</div>
                  <div className="text-xs text-gray-600">{new Date(r.created_at).toLocaleDateString()}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-8">
        {['python', 'java', 'cpp', 'c'].map((l) => (
          <Link
            key={l}
            to={`/language/${l}`}
            className="card card-glow p-4 text-center text-sm font-medium text-gray-300 hover:text-white capitalize"
          >
            {l === 'cpp' ? 'C++' : l}
          </Link>
        ))}
      </div>
    </div>
  )
}
