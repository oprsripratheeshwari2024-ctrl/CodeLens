"""
CodeLens backend entrypoint.

Run locally with:
    uvicorn main:app --reload --port 8000

Expects an optional .env file (copy .env.example) with OPENAI_API_KEY.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db
from api.routes import router

app = FastAPI(title="CodeLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://code-lens-dcajqmrtc-oprsripratheeshwari2024-ctrls-projects.vercel.app",
        "https://code-lens-ten-mu.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "service": "CodeLens API"}


app.include_router(router)