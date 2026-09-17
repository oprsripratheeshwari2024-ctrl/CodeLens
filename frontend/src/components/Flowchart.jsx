import React, { useMemo, useState } from 'react'
import ReactFlow, { Background, Controls, MiniMap } from 'reactflow'
import 'reactflow/dist/style.css'
import { Workflow, X } from 'lucide-react'
import api from '../services/api.js'

const KIND_COLOR = {
  start: '#22c55e',
  end: '#ef4444',
  loop: '#8b5cf6',
  condition: '#f59e0b',
  call: '#38bdf8',
  step: '#a78bfa',
}

function styledNodes(nodes) {
  return nodes.map((n) => ({
    ...n,
    style: {
      background: '#1a1a2e',
      border: `1.5px solid ${KIND_COLOR[n.data.kind] || '#8b5cf6'}`,
      borderRadius: 10,
      color: '#e5e5ef',
      fontSize: 12,
      padding: 8,
      width: 190,
    },
  }))
}

export default function Flowchart({ flowchart, language }) {
  const [selected, setSelected] = useState(null)
  const [stepInfo, setStepInfo] = useState(null)
  const [loadingStep, setLoadingStep] = useState(false)

  const nodes = useMemo(() => styledNodes(flowchart?.nodes || []), [flowchart])
  const edges = useMemo(
    () => (flowchart?.edges || []).map((e) => ({ ...e, animated: true, style: { stroke: '#6d28d9' } })),
    [flowchart]
  )

  if (!flowchart) return null

  const onNodeClick = async (_, node) => {
    if (node.data.kind === 'start' || node.data.kind === 'end') {
      setSelected(node)
      setStepInfo(null)
      return
    }
    setSelected(node)
    setLoadingStep(true)
    try {
      const info = await api.flowStepExplain(node.data.label, node.data.code, language)
      setStepInfo(info)
    } catch {
      setStepInfo({ explanation: 'Could not reach the backend to explain this step.' })
    } finally {
      setLoadingStep(false)
    }
  }

  return (
    <div className="card p-5 fade-in">
      <div className="flex items-center gap-2 mb-3">
        <Workflow size={16} className="text-primary" />
        <h3 className="font-semibold text-white">Program Flow Visualization</h3>
      </div>

      <div className="relative h-[420px] bg-bg rounded-xl border border-border overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={onNodeClick}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background color="#26263f" gap={18} />
          <Controls />
          <MiniMap
            nodeColor={(n) => KIND_COLOR[n.data?.kind] || '#8b5cf6'}
            maskColor="rgba(10,10,15,0.7)"
            style={{ background: '#131320' }}
          />
        </ReactFlow>

        {selected && (
          <div className="absolute top-3 right-3 w-72 bg-surface border border-primary/30 rounded-xl p-4 shadow-glow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-white">{selected.data.label}</span>
              <button onClick={() => setSelected(null)} className="text-gray-500 hover:text-white">
                <X size={14} />
              </button>
            </div>
            {selected.data.code && (
              <pre className="text-xs bg-bg border border-border rounded p-2 mb-2 overflow-x-auto font-mono text-gray-300">
                {selected.data.code}
              </pre>
            )}
            {loadingStep ? (
              <p className="text-xs text-gray-500">Explaining…</p>
            ) : stepInfo ? (
              <p className="text-xs text-gray-400 leading-relaxed">{stepInfo.explanation}</p>
            ) : (
              <p className="text-xs text-gray-500">Program {selected.data.kind === 'start' ? 'begins' : 'ends'} here.</p>
            )}
          </div>
        )}
      </div>
      <p className="text-xs text-gray-600 mt-2">Click any node to see what happens and why that step exists.</p>
    </div>
  )
}
