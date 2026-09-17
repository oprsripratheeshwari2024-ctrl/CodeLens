# CodeLens

AI-Powered Code Analysis, Debugging, Explanation and Program Flow Visualization System — for Python, Java, C++, and C.

CodeLens analyzes source code and explains **what it does, why each part exists, what's wrong with it, how to fix it, and how it executes step by step** — with an interactive flowchart, a code-quality score, and downloadable PDF reports.

---

## 1. What's actually implemented

This is a real, working full-stack app — not a static mockup. Every feature listed below runs against real logic:

| Feature | How it works |
|---|---|
| Email-only login | FastAPI + SQLite, no password/OTP |
| Python analysis | Python's built-in `ast` module — real structural parsing, real syntax-error line numbers |
| Java / C++ / C analysis | Built-in heuristic/regex analyzer (functional fallback). If `clang`/`clang++` is on your PATH, C/C++ also get real compiler diagnostics automatically |
| Error & bug detection | Deterministic, from the analyzer above (division-by-zero, unreachable code, unused variables, unbalanced braces, possible infinite loops, memory-leak risk, etc.) |
| Explanations, fixes, improvement suggestions | OpenAI API if you set `OPENAI_API_KEY`; otherwise a deterministic template fallback (clearly labeled in the UI) so the app never breaks without a key |
| Corrected code | AI-suggested fix, **re-validated by the same deterministic parser** before being labeled "Parser Validation: Passed" |
| Flowchart | Generated from the parsed code structure, rendered with React Flow; click any node to see what it does and why |
| Quality score / complexity / security | Calculated from real analysis results (not AI), so it's reproducible |
| History | Stored in SQLite, reopenable |
| PDF report | Generated server-side with `reportlab` |
| Reviews | Stored in SQLite |

**Note on Java/C++/C parsing:** the spec calls for JavaParser and Clang/LibTooling. Those are separate toolchains (JVM / native compiler) that can't be bundled into a pip install, so CodeLens ships a fully working heuristic analyzer as the default for those three languages, with an automatic upgrade path to real `clang`/`clang++` diagnostics if you have LLVM installed. Python uses the real `ast` parser out of the box since it ships with Python itself. See the comments at the top of each file in `backend/analyzers/` for how to wire in the full JavaParser/Clang toolchains later.

---

## 2. Requirements (Windows 11)

- **Python 3.12** — https://www.python.org/downloads/ (check "Add python.exe to PATH" during install)
- **Node.js 18+** — https://nodejs.org/
- **Git** (optional, if you want version control)
- *(Optional)* An OpenAI API key, for richer AI explanations/fixes — https://platform.openai.com/api-keys
- *(Optional)* LLVM/Clang, if you want real compiler diagnostics for C/C++ — https://releases.llvm.org/

---

## 3. Setup

Open **PowerShell** or **Command Prompt** and unzip the project, then:

### Backend

```powershell
cd CodeLens\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
```

Open `backend\.env` and add your OpenAI key if you have one (optional — the app works without it):

```
OPENAI_API_KEY=sk-...
```

Run the backend:

```powershell
uvicorn main:app --reload --port 8000
```

Backend is now live at **http://localhost:8000**. You can check http://localhost:8000/docs for the interactive API docs.

### Frontend

Open a **second** PowerShell window:

```powershell
cd CodeLens\frontend
npm install
npm run dev
```

Frontend is now live at **http://localhost:3000**.

### Use it

Open **http://localhost:3000** in Chrome or Edge, enter any email, and start analyzing code.

---

## 4. Project structure

```
CodeLens/
├── frontend/          React + Vite + Tailwind + Monaco + React Flow
│   └── src/
│       ├── components/   CodeEditor, Flowchart, Errors/Quality/Explanation panels, Sidebar
│       ├── pages/        Login, Dashboard, Workspace, History, Review
│       └── services/     api.js (talks to the FastAPI backend)
├── backend/           FastAPI + SQLite
│   ├── api/routes.py      all REST endpoints
│   ├── analyzers/         python_analyzer.py (real AST), java/cpp/c_analyzer.py (heuristic)
│   ├── ai/ai_service.py   OpenAI wrapper with template fallback
│   ├── services/          flowchart, quality scoring, PDF report generation
│   └── database/db.py     SQLite schema + queries
├── database/           codelens.db is created here on first run
├── .env.example
└── .gitignore
```

---

## 5. Sample code for testing

Each language workspace pre-fills a small working sample when you open it — click **Analyze Code** immediately to see the full pipeline run, or paste in your own code (including broken code) to see error detection in action. Try removing a closing bracket or dividing by zero to see it flagged.

---

## 6. Known limitations (stated honestly)

- Java/C++/C error detection is heuristic-based by default (real AST-level parsing for those needs JavaParser / Clang installed separately — see above).
- The security scanner is a lightweight static check, not a full security audit.
- AI features need `OPENAI_API_KEY`; without it, CodeLens uses clearly-labeled template explanations instead so nothing ever breaks.
- Built for local single-user use on `localhost`, per the project brief — no multi-tenant auth hardening.
