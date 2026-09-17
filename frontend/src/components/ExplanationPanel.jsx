import React from 'react'
import { Sparkles } from 'lucide-react'

export default function ExplanationPanel({ explanation, components }) {
  if (!explanation) return null

  const groups = [
    { key: 'functions', label: 'Functions', reason: 'Groups reusable logic into one named block.' },
    { key: 'classes', label: 'Classes', reason: 'Bundles related data and behavior together.' },
    { key: 'loops', label: 'Loops', reason: 'Repeats an operation without duplicating code.' },
    { key: 'conditions', label: 'Conditions', reason: 'Lets the program branch based on a check.' },
    { key: 'variables', label: 'Variables', reason: 'Stores a value for later use in the program.' },
    { key: 'imports', label: 'Imports', reason: 'Brings in functionality from another module/library.' },
  ]

  return (
    <div className="card p-5 fade-in">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles size={16} className="text-primary" />
        <h3 className="font-semibold text-white">Code Explanation</h3>
        {explanation.source === 'template' && (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface2 text-gray-500 border border-border">
            template
          </span>
        )}
      </div>
      <p className="text-sm text-gray-300 leading-relaxed mb-5">{explanation.summary}</p>

      <div className="grid sm:grid-cols-2 gap-3">
        {groups.map((g) => {
          const items = components?.[g.key] || []
          if (items.length === 0) return null
          return (
            <div key={g.key} className="bg-surface2 border border-border rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-primary-light">{g.label}</span>
                <span className="text-xs text-gray-500">{items.length}</span>
              </div>
              <p className="text-xs text-gray-500 mb-2">{g.reason}</p>
              <div className="flex flex-wrap gap-1">
                {items.slice(0, 8).map((it, idx) => (
                  <span key={idx} className="text-[11px] px-2 py-0.5 rounded bg-bg border border-border text-gray-400">
                    {it.name || `line ${it.line}`}
                  </span>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
