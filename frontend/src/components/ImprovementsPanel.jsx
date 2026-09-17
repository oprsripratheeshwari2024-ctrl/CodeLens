import React from 'react'
import { Lightbulb } from 'lucide-react'

export default function ImprovementsPanel({ improvements = [] }) {
  if (improvements.length === 0) return null
  return (
    <div className="card p-5 fade-in">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb size={16} className="text-primary" />
        <h3 className="font-semibold text-white">Improvement Suggestions</h3>
      </div>
      <ul className="space-y-2">
        {improvements.map((s, i) => (
          <li key={i} className="text-sm text-gray-300 flex gap-2">
            <span className="text-primary mt-0.5">•</span>
            <span>{s}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
