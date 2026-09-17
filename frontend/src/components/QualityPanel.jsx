import React from 'react'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts'
import { Gauge } from 'lucide-react'

export default function QualityPanel({ quality }) {
  if (!quality) return null

  const data = [
    { name: 'Readability', value: quality.readability },
    { name: 'Maintainability', value: quality.maintainability },
    { name: 'Complexity', value: quality.complexity },
    { name: 'Security', value: quality.security },
  ]

  const colorFor = (v) => (v >= 80 ? '#22c55e' : v >= 50 ? '#f59e0b' : '#ef4444')

  return (
    <div className="card p-5 fade-in">
      <div className="flex items-center gap-2 mb-1">
        <Gauge size={16} className="text-primary" />
        <h3 className="font-semibold text-white">Code Quality</h3>
      </div>
      <div className="flex items-end gap-2 mb-4">
        <span className="text-4xl font-bold text-white">{quality.overall}</span>
        <span className="text-gray-500 mb-1">/ 100</span>
      </div>

      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
            <XAxis type="number" domain={[0, 100]} hide />
            <YAxis dataKey="name" type="category" width={100} tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} />
            <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={14}>
              {data.map((d, i) => (
                <Cell key={i} fill={colorFor(d.value)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {quality.complexity_summary && (
        <div className="grid grid-cols-3 gap-2 mt-2 text-center">
          <div className="bg-surface2 border border-border rounded-lg py-2">
            <div className="text-xs text-gray-500">Complexity</div>
            <div className="text-sm font-semibold text-primary-light">{quality.complexity_summary.overall_label}</div>
          </div>
          <div className="bg-surface2 border border-border rounded-lg py-2">
            <div className="text-xs text-gray-500">Loops</div>
            <div className="text-sm font-semibold text-white">{quality.complexity_summary.nested_loops}</div>
          </div>
          <div className="bg-surface2 border border-border rounded-lg py-2">
            <div className="text-xs text-gray-500">Conditions</div>
            <div className="text-sm font-semibold text-white">{quality.complexity_summary.conditions}</div>
          </div>
        </div>
      )}
    </div>
  )
}
