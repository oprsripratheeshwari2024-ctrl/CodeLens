import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Play, Eraser, FileDown, Info } from 'lucide-react'
import api from '../services/api.js'
import CodeEditor from '../components/CodeEditor.jsx'
import ExplanationPanel from '../components/ExplanationPanel.jsx'
import LineByLineExplanation from '../components/LineByLineExplanation.jsx'
import ErrorsPanel from '../components/ErrorsPanel.jsx'
import CorrectedCodePanel from '../components/CorrectedCodePanel.jsx'
import Flowchart from '../components/Flowchart.jsx'
import QualityPanel from '../components/QualityPanel.jsx'
import ImprovementsPanel from '../components/ImprovementsPanel.jsx'
import SecurityPanel from '../components/SecurityPanel.jsx'

const LANG_LABEL = { python: 'Python', java: 'Java', cpp: 'C++', c: 'C' }

const SAMPLE = {
  python: `def average(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total / len(numbers)\n\nresult = average([1, 2, 3, 4])\nprint(result)\n`,
  java: `public class Main {\n    public static void main(String[] args) {\n        int total = 0;\n        for (int i = 0; i < 5; i++) {\n            total += i;\n        }\n        System.out.println(total);\n    }\n}\n`,
  cpp: `#include <iostream>\nusing namespace std;\n\nint main() {\n    int total = 0;\n    for (int i = 0; i < 5; i++) {\n        total += i;\n    }\n    cout << total << endl;\n    return 0;\n}\n`,
  c: `#include <stdio.h>\n\nint main() {\n    int total = 0;\n    for (int i = 0; i < 5; i++) {\n        total += i;\n    }\n    printf("%d\\n", total);\n    return 0;\n}\n`,
}

export default function Workspace({ user }) {
  const { lang } = useParams()
  const [code, setCode] = useState(SAMPLE[lang] || '')
  const [mode, setMode] = useState('beginner')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAnalyze = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.analyze(user.user_id, lang, code, mode)
      if (res.error) {
        setError(`${res.message} ${res.reason || ''}`)
        setResult(null)
      } else {
        setResult(res)
      }
    } catch (err) {
      setError('Could not reach the CodeLens backend. Is it running on localhost:8000?')
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    setCode('')
    setResult(null)
    setError('')
  }

  const handleApplyFix = (fixedCode) => {
    setCode(fixedCode)
  }

  const downloadReport = () => {
    if (!result?.analysis_id) return
    window.open(api.reportUrl(user.user_id, result.analysis_id), '_blank')
  }

  return (
    <div className="p-8 max-w-6xl mx-auto fade-in">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h1 className="text-xl font-bold text-white">{LANG_LABEL[lang]} Code Analyzer</h1>
        <div className="flex items-center gap-1 bg-surface2 border border-border rounded-lg p-1">
          <button
            onClick={() => setMode('beginner')}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${mode === 'beginner' ? 'bg-primary text-white' : 'text-gray-400'}`}
          >
            Beginner Mode
          </button>
          <button
            onClick={() => setMode('developer')}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${mode === 'developer' ? 'bg-primary text-white' : 'text-gray-400'}`}
          >
            Developer Mode
          </button>
        </div>
      </div>

      <CodeEditor language={lang} value={code} onChange={setCode} />

      <div className="flex items-center gap-3 mt-4">
        <button onClick={handleAnalyze} disabled={loading} className="btn-primary px-5 py-2.5 text-sm flex items-center gap-2 disabled:opacity-60">
          <Play size={15} />
          {loading ? 'Analyzing…' : 'Analyze Code'}
        </button>
        <button onClick={handleClear} className="btn-secondary px-5 py-2.5 text-sm flex items-center gap-2">
          <Eraser size={15} />
          Clear
        </button>
        {result?.analysis_id && (
          <button onClick={downloadReport} className="btn-secondary px-5 py-2.5 text-sm flex items-center gap-2 ml-auto">
            <FileDown size={15} />
            Generate Report
          </button>
        )}
      </div>

      {error && (
        <div className="mt-4 card p-4 border-danger/40 text-sm text-danger">{error}</div>
      )}

      {result?.analyzer_note && (
        <div className="mt-4 flex items-start gap-2 text-xs text-gray-500 bg-surface2 border border-border rounded-lg p-3">
          <Info size={14} className="mt-0.5 shrink-0" />
          <span>{result.analyzer_note}</span>
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-5">
          <ExplanationPanel explanation={result.explanation} components={result.components} />
          <LineByLineExplanation lines={result.line_explanations} />
          <ErrorsPanel errors={result.errors} issues={result.issues} />
          <CorrectedCodePanel fix={result.fix} originalCode={code} onApplyFix={handleApplyFix} />
          <Flowchart flowchart={result.flowchart} language={lang} />
          <div className="grid md:grid-cols-2 gap-5">
            <QualityPanel quality={result.quality} />
            <SecurityPanel security={result.security} />
          </div>
          <ImprovementsPanel improvements={result.improvements} />
        </div>
      )}
    </div>
  )
}
