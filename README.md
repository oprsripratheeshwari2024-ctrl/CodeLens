# CodeLens
Run: `cd backend && pip install -r requirements.txt && cp .env.example .env && uvicorn main:app --reload` -> http://localhost:8000
Login: just enter your email and click Continue (no OTP).
AI Tools / AI fix / Converter need OPENAI_API_KEY in backend/.env (rule-based fallback for fixes).
Docker: `docker build -t codelens . && docker run -p 8000:8000 codelens` (deploy on Render/Railway the same way).
