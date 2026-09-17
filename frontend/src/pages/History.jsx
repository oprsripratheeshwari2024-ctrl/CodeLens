import React, { useEffect, useState } from 'react'
import { Clock, ChevronRight, FileDown } from 'lucide-react'
import api from '../services/api.js'
import ExplanationPanel from '../components/ExplanationPanel.jsx'
import LineByLineExplanation from '../components/LineByLineExplanation.jsx'
import ErrorsPanel from '../components/ErrorsPanel.jsx'
import QualityPanel from '../components/QualityPanel.jsx'

export default function History({ user }) {
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.history(user.user_id)
      .then((d) => setItems(d.history))
      .catch(() => setError('Could not reach the CodeLens backend.'))
  }, [user.user_id])

  const openItem = async (id) => {
    try {
      const detail = await api.historyDetail(user.user_id, id)
      setSelected(detail)
    } catch {
      setError('Could not load this analysis.')
    }
  }

  return (
    <div className="p-8 max-w-6xl mx-auto fade-in">
      <div className="flex items-center gap-2 mb-6">
        <Clock size={18} className="text-primary" />
        <h1 className="text-xl font-bold text-white">Analysis History</h1>
      </div>

      {error && <p className="text-danger text-sm mb-4">{error}</p>}

      <div className="grid md:grid-cols-[280px_1fr] gap-5">
        <div className="card p-2 h-fit">
          {items.length === 0 ? (
            <p className="text-sm text-gray-500 p-3">No analyses yet.</p>
          ) : (
            items.map((it) => (
              <button
                key={it.id}
                onClick={() => openItem(it.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg flex items-center justify-between text-sm mb-1 transition-colors ${
                  selected?.id === it.id ? 'bg-primary/15 text-primary-light' : 'hover:bg-surface2 text-gray-300'
                }`}
              >
                <div>
                  <div className="font-medium capitalize">{it.language}</div>
                  <div className="text-xs text-gray-500">{new Date(it.created_at).toLocaleDateString()}</div>
                </div>
                <ChevronRight size={14} className="opacity-50" />
              </button>
            ))
          )}
        </div>

        <div>
          {!selected ? (
            <div className="card p-8 text-center text-sm text-gray-500">
              Select an analysis on the left to reopen its results.
            </div>
          ) : (
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-white font-semibold capitalize">{selected.language} — {new Date(selected.created_at).toLocaleString()}</h2>
                <a
                  href={api.reportUrl(user.user_id, selected.id)}
                  target="_blank" rel="noreferrer"
                  className="btn-secondary px-3 py-1.5 text-xs flex items-center gap-1.5"
                >
                  <FileDown size={13} /> Report
                </a>
              </div>
              <ExplanationPanel explanation={selected.result.explanation} components={selected.result.components} />
              <LineByLineExplanation lines={selected.result.line_explanations} />
              <ErrorsPanel errors={selected.result.errors} issues={selected.result.issues} />
              <QualityPanel quality={selected.result.quality} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
