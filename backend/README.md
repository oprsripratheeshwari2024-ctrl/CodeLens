# CodeLens Backend

FastAPI service. See the top-level README.md for full setup instructions.

Quick start:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env
uvicorn main:app --reload --port 8000
```

API docs available at http://localhost:8000/docs once running.

## Endpoints

- `POST /api/login` — email-only login, returns `user_id`
- `GET  /api/dashboard/{user_id}` — dashboard stats + recent history
- `POST /api/analyze` — full pipeline (explanation, errors, fix, flowchart, quality, security, improvements)
- `POST /api/explain`, `/api/detect-errors`, `/api/fix-code`, `/api/generate-flow`, `/api/improvements` — individual pipeline stages
- `POST /api/flow-step-explain` — explains a single flowchart node on click
- `GET  /api/history?user_id=` — list past analyses
- `GET  /api/history/{id}?user_id=` — full stored result for one analysis
- `GET  /api/report/{id}?user_id=` — downloads a PDF report
- `POST /api/review` — submit a star rating + feedback
