import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  Code2, LayoutDashboard, History, Star, ChevronDown,
  FileCode, LogOut, Menu,
} from 'lucide-react'

const LANGUAGES = [
  { key: 'python', label: 'Python' },
  { key: 'java', label: 'Java' },
  { key: 'cpp', label: 'C++' },
  { key: 'c', label: 'C' },
]

export default function Sidebar({ onLogout }) {
  const [collapsed, setCollapsed] = useState(false)
  const [langOpen, setLangOpen] = useState(true)

  const linkClass = ({ isActive }) =>
    `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
      isActive ? 'bg-primary/15 text-primary-light border border-primary/30' : 'text-gray-400 hover:bg-surface2 hover:text-white'
    }`

  return (
    <aside
      className={`h-screen bg-surface border-r border-border flex flex-col transition-all duration-200 ${
        collapsed ? 'w-16' : 'w-60'
      }`}
    >
      <div className="flex items-center justify-between px-4 py-4 border-b border-border">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-dark flex items-center justify-center">
              <Code2 size={16} className="text-white" />
            </div>
            <span className="font-bold text-white tracking-tight">CODELENS</span>
          </div>
        )}
        <button onClick={() => setCollapsed(!collapsed)} className="text-gray-500 hover:text-white">
          <Menu size={18} />
        </button>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <NavLink to="/" end className={linkClass}>
          <LayoutDashboard size={17} />
          {!collapsed && <span>Dashboard</span>}
        </NavLink>

        <button
          onClick={() => setLangOpen(!langOpen)}
          className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-surface2 hover:text-white"
        >
          <span className="flex items-center gap-2.5">
            <FileCode size={17} />
            {!collapsed && <span>Languages</span>}
          </span>
          {!collapsed && <ChevronDown size={14} className={`transition-transform ${langOpen ? '' : '-rotate-90'}`} />}
        </button>
        {langOpen && !collapsed && (
          <div className="ml-4 pl-3 border-l border-border space-y-1">
            {LANGUAGES.map((l) => (
              <NavLink key={l.key} to={`/language/${l.key}`} className={linkClass}>
                <span className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                <span>{l.label}</span>
              </NavLink>
            ))}
          </div>
        )}

        <NavLink to="/history" className={linkClass}>
          <History size={17} />
          {!collapsed && <span>Analysis History</span>}
        </NavLink>
        <NavLink to="/review" className={linkClass}>
          <Star size={17} />
          {!collapsed && <span>Review</span>}
        </NavLink>
      </nav>

      <div className="px-3 py-4 border-t border-border">
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-surface2 hover:text-danger"
        >
          <LogOut size={17} />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </aside>
  )
}
