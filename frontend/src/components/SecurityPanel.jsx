import React from 'react'
import { ShieldCheck, ShieldAlert } from 'lucide-react'

export default function SecurityPanel({ security }) {
  if (!security) return null
  const clear = security.status === 'clear'
  return (
    <div className="card p-5 fade-in">
      <div className="flex items-center gap-2 mb-3">
        {clear ? <ShieldCheck size={16} className="text-success" /> : <ShieldAlert size={16} className="text-warning" />}
        <h3 className="font-semibold text-white">Security Status</h3>
      </div>
      {clear ? (
        <p className="text-sm text-success">✓ {security.message}</p>
      ) : (
        <div className="space-y-2">
          {security.findings?.map((f, i) => (
            <div key={i} className="bg-surface2 border border-warning/30 rounded-lg p-3">
              <p className="text-sm text-warning font-medium">⚠ {f.type}</p>
              <p className="text-xs text-gray-400 mt-1">{f.description}</p>
            </div>
          ))}
          <p className="text-xs text-gray-600">{security.note}</p>
        </div>
      )}
    </div>
  )
}
