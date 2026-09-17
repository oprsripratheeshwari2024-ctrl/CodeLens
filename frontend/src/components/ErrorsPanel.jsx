import React from 'react'
import { AlertTriangle, HelpCircle, CheckCircle2 } from 'lucide-react'

const SEV_CLASS = { High: 'badge-high', Medium: 'badge-medium', Low: 'badge-low' }

export default function ErrorsPanel({ errors = [], issues = [] }) {
  return (
    <div className="card p-5 fade-in">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle size={16} className="text-danger" />
        <h3 className="font-semibold text-white">Errors & Bugs</h3>
      </div>

      {errors.length === 0 && issues.length === 0 && (
        <div className="flex items-center gap-2 text-sm text-success">
          <CheckCircle2 size={16} />
          No confirmed errors or potential issues detected.
        </div>
      )}

      {errors.length > 0 && (
        <div className="space-y-3 mb-5">
          <p className="text-xs uppercase tracking-wide text-gray-500 font-semibold">Confirmed Errors</p>
          {errors.map((e, i) => (
            <div key={i} className="bg-surface2 border border-border rounded-lg p-3.5">
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <span className={`text-[11px] px-2 py-0.5 rounded-full ${SEV_CLASS[e.severity] || 'badge-medium'}`}>
                  {e.severity}
                </span>
                <span className="text-sm font-medium text-white">{e.type}</span>
                <span className="text-xs text-gray-500">Line {e.line}</span>
              </div>
              <p className="text-sm text-gray-300 mb-1">{e.problem}</p>
              {e.why && <p className="text-xs text-gray-500 mb-1"><span className="text-gray-400">Why:</span> {e.why}</p>}
              {e.how_to_fix && <p className="text-xs text-primary-light"><span className="text-gray-400">Fix:</span> {e.how_to_fix}</p>}
            </div>
          ))}
        </div>
      )}

      {issues.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs uppercase tracking-wide text-gray-500 font-semibold flex items-center gap-1.5">
            <HelpCircle size={13} /> Potential Issues (not confirmed)
          </p>
          {issues.map((it, i) => (
            <div key={i} className="bg-surface2/60 border border-border/60 rounded-lg p-3.5">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-[11px] px-2 py-0.5 rounded-full badge-medium">Potential Issue</span>
                <span className="text-sm font-medium text-gray-200">{it.type}</span>
                <span className="text-xs text-gray-500">Line {it.line}</span>
              </div>
              <p className="text-sm text-gray-400">{it.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
