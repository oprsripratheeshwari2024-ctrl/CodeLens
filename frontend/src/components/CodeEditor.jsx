import React from 'react'
import Editor from '@monaco-editor/react'

const MONACO_LANG = { python: 'python', java: 'java', cpp: 'cpp', c: 'c' }

export default function CodeEditor({ language, value, onChange, errorLines = [] }) {
  return (
    <div className="rounded-xl overflow-hidden border border-border">
      <Editor
        height="420px"
        language={MONACO_LANG[language] || 'plaintext'}
        theme="vs-dark"
        value={value}
        onChange={(v) => onChange(v ?? '')}
        options={{
          fontSize: 14,
          fontFamily: 'JetBrains Mono, Fira Code, monospace',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          padding: { top: 14 },
          automaticLayout: true,
        }}
      />
    </div>
  )
}
