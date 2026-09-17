import React, { useState } from 'react'
import { ListTree, ChevronDown, ChevronRight, Sparkles } from 'lucide-react'

/**
 * Renders the submitted code one line at a time, with an inline
 * "Why this line?" toggle per row that expands into the explanation
 * returned by the backend (/analyze -> line_explanations, or the
 * standalone /explain-lines endpoint).
 *
 * `lines` shape: [{ line: 1, code: 'def foo():', why: '...', source: 'ai'|'template' }, ...]
 */
export default function LineByLineExplanation({ lines }) {
  const [openLine, setOpenLine] = useState(null)
  const [expandAll, setExpandAll] = useState(false)

  if (!lines || lines.length === 0) return null

  const toggle = (lineNo) => {
    setOpenLine((prev) => (prev === lineNo ? null : lineNo))
  }

  return (
    <div className="card p-5 fade-in">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <ListTree size={16} className="text-primary" />
          <h3 className="font-semibold text-white">Line-by-Line Explanation</h3>
        </div>
        <button
          onClick={() => setExpandAll((v) => !v)}
          className="text-xs px-2.5 py-1 rounded-md bg-surface2 border border-border text-gray-400 hover:text-white transition-colors"
        >
          {expandAll ? 'Collapse all' : 'Expand all'}
        </button>
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        {lines.map((row) => {
          const isOpen = expandAll || openLine === row.line
          const isBlank = !row.code.trim()
          return (
            <div key={row.line} className="border-b border-border last:border-b-0">
              <button
                onClick={() => !expandAll && toggle(row.line)}
                className="w-full flex items-start gap-3 px-3 py-1.5 text-left hover:bg-surface2/60 transition-colors group"
              >
                <span className="text-[11px] text-gray-600 w-7 shrink-0 text-right pt-0.5 select-none">
                  {row.line}
                </span>
                <code className="text-xs font-mono text-gray-300 whitespace-pre flex-1 pt-0.5">
                  {isBlank ? ' ' : row.code}
                </code>
                {!isBlank && (
                  <span className="shrink-0 flex items-center gap-1 text-[11px] text-primary-light opacity-70 group-hover:opacity-100">
                    {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                    Why this line?
                  </span>
                )}
              </button>

              {isOpen && !isBlank && (
                <div className="px-3 pb-2.5 pl-12 flex items-start gap-2 fade-in">
                  <Sparkles size={12} className="text-primary mt-0.5 shrink-0" />
                  <p className="text-xs text-gray-400 leading-relaxed">
                    {row.why}
                    {row.source === 'template' && (
                      <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded-full bg-surface2 text-gray-500 border border-border align-middle">
                        template
                      </span>
                    )}
                  </p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
