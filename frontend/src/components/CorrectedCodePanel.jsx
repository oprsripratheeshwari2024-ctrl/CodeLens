import React from 'react'
import { GitCompare, CheckCircle2, XCircle, Wrench } from 'lucide-react'

export default function CorrectedCodePanel({ fix, originalCode, onApplyFix }) {
  if (!fix) return null

  if (!fix.fixed_code) {
    return (
      <div className="card p-5 fade-in">
        <div className="flex items-center gap-2 mb-2">
          <GitCompare size={16} className="text-primary" />
          <h3 className="font-semibold text-white">Corrected Code</h3>
        </div>
        <p className="text-sm text-gray-500 mb-4">{fix.notes}</p>

        {fix.fix_steps && fix.fix_steps.length > 0 && (
          <div className="space-y-2.5">
            <p className="text-xs uppercase tracking-wide text-gray-500 font-semibold flex items-center gap-1.5">
              <Wrench size={12} /> How to Fix — Step by Step
            </p>
            {fix.fix_steps.map((s, i) => (
              <div key={i} className="bg-surface2 border border-border rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] px-2 py-0.5 rounded-full bg-primary/15 text-primary-light border border-primary/30">
                    Line {s.line}
                  </span>
                  <span className="text-xs text-gray-400">{s.problem}</span>
                </div>
                <p className="text-xs text-gray-300">{s.how_to_fix}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="card p-5 fade-in">
      <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <GitCompare size={16} className="text-primary" />
          <h3 className="font-semibold text-white">Corrected Code</h3>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface2 text-gray-500 border border-border">
            {fix.source === 'ai' ? 'AI Suggested Fix' : 'Rule-Based Fix'}
          </span>
        </div>
        {fix.parser_validation && (
          <span className={`flex items-center gap-1 text-xs ${fix.parser_validation === 'Passed' ? 'text-success' : 'text-danger'}`}>
            {fix.parser_validation === 'Passed' ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
            Parser Validation: {fix.parser_validation}
          </span>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-3 mb-4">
        <div>
          <p className="text-xs text-danger mb-1.5 font-medium">❌ Original</p>
          <pre className="bg-surface2 border border-border rounded-lg p-3 text-xs text-gray-400 overflow-x-auto max-h-64 font-mono">
            {originalCode}
          </pre>
        </div>
        <div>
          <p className="text-xs text-success mb-1.5 font-medium">✅ Corrected</p>
          <pre className="bg-surface2 border border-success/30 rounded-lg p-3 text-xs text-gray-200 overflow-x-auto max-h-64 font-mono">
            {fix.fixed_code}
          </pre>
        </div>
      </div>

      {fix.fix_steps && fix.fix_steps.length > 0 && (
        <div className="space-y-2 mb-4">
          <p className="text-xs uppercase tracking-wide text-gray-500 font-semibold flex items-center gap-1.5">
            <Wrench size={12} /> What Changed and Why
          </p>
          {fix.fix_steps.map((s, i) => (
            <div key={i} className="bg-surface2/60 border border-border/60 rounded-lg p-2.5">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/15 text-primary-light border border-primary/30">
                  Line {s.line}
                </span>
                <span className="text-xs text-gray-400">{s.problem}</span>
              </div>
              <p className="text-xs text-gray-500">{s.how_to_fix}</p>
            </div>
          ))}
        </div>
      )}

      <button onClick={() => onApplyFix(fix.fixed_code)} className="btn-primary px-4 py-2 text-sm">
        Apply Fix
      </button>
    </div>
  )
}
