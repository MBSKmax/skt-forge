"""
AI Scaffold Agent - Backend API (FastAPI + Groq)
==================================================
Ye backend Phase 1 ka core hai: frontend se prompt aata hai,
Groq se 3 specialist calls hoti hain, JSON mein code wapas jata hai.

Run (PowerShell):
    $env:GROQ_API_KEY="your_key_here"
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Test: http://localhost:8000/docs (Swagger UI khud test karne ke liye)
"""

import os
import re
import sys
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-120b"  # llama-3.3-70b-versatile deprecated hai
REQUEST_TIMEOUT = 120

app = FastAPI(title="SKT-Forge API")

# Local dev + Vercel frontend dono se calls allow karne ke liye.
# Production mein allow_origins ko apni actual frontend URL tak limit kar dein.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://skt-forge.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# SPECIALIST SYSTEM PROMPTS (agent.py se same)
# ---------------------------------------------------------------------------

FRONTEND_SYSTEM = """You are a senior React frontend developer.
You ONLY write frontend code. Do not write backend or database code.
Rules:
- Use React functional components with hooks (no imports needed, React is global).
- Use Tailwind CSS classes for styling.
- Assume the backend API base URL is `/api`.
- Component must be a single function that can be rendered directly.
- Output ONLY one code block in this exact format:

```jsx
// filename: ComponentName.jsx
<code here>
```

No explanations before or after the code block."""

BACKEND_SYSTEM = """You are a senior backend developer using FastAPI (Python).
You ONLY write backend API code. Do not write frontend or raw SQL schema code.
Rules:
- Use FastAPI with Pydantic models for request/response validation.
- Assume a SQLAlchemy-style database session dependency named `get_db`.
- Include realistic endpoint(s) for the requested feature.
- Output ONLY one code block in this exact format:

```python
# filename: route_name.py
<code here>
```

No explanations before or after the code block."""

DATABASE_SYSTEM = """You are a senior database engineer.
You ONLY write SQL schema code (PostgreSQL syntax).
Rules:
- Write CREATE TABLE statements with proper types, primary keys, and constraints.
- Add sensible indexes where appropriate.
- Output ONLY one code block in this exact format:

```sql
-- filename: schema_name.sql
<code here>
```

No explanations before or after the code block."""

AGENTS = {
    "database": {"system": DATABASE_SYSTEM, "ext_hint": "sql"},
    "backend": {"system": BACKEND_SYSTEM, "ext_hint": "py"},
    "frontend": {"system": FRONTEND_SYSTEM, "ext_hint": "jsx"},
}


# ---------------------------------------------------------------------------
# REQUEST / RESPONSE MODELS
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    prompt: str


class FileResult(BaseModel):
    filename: str
    code: str


class GenerateResponse(BaseModel):
    feature: str
    generated_at: str
    model: str
    frontend: FileResult
    backend: FileResult
    database: FileResult


# ---------------------------------------------------------------------------
# CORE LOGIC
# ---------------------------------------------------------------------------

def call_groq(system_prompt: str, user_prompt: str) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY set nahi hai server pe. Environment variable check karein.",
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Groq se connect nahi ho paya.")
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Groq request timeout ho gayi.")

    if resp.status_code == 401:
        raise HTTPException(status_code=500, detail="Invalid GROQ_API_KEY.")
    if resp.status_code == 429:
        raise HTTPException(status_code=429, detail="Rate limit lag gayi, thoda ruk kar try karein.")
    resp.raise_for_status()

    data = resp.json()
    return data["choices"][0]["message"]["content"]


def extract_code_block(raw_text: str, ext_hint: str):
    pattern = r"```[a-zA-Z]*\n(.*?)```"
    match = re.search(pattern, raw_text, re.DOTALL)
    if not match:
        return f"generated.{ext_hint}", raw_text.strip()

    block = match.group(1).strip()
    lines = block.split("\n")

    filename_pattern = re.compile(r"(?:#|//|--)\s*filename:\s*(\S+)", re.IGNORECASE)
    fm = filename_pattern.match(lines[0].strip())
    if fm:
        return fm.group(1), "\n".join(lines[1:]).strip()

    return f"generated.{ext_hint}", block


def run_specialist(role: str, user_prompt: str) -> FileResult:
    cfg = AGENTS[role]
    raw = call_groq(cfg["system"], user_prompt)
    filename, code = extract_code_block(raw, cfg["ext_hint"])
    return FileResult(filename=filename, code=code)


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.get("/")
def health_check():
    return {"status": "ok", "message": "SKT-Forge API chal raha hai"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate_scaffold(req: GenerateRequest):
    if not req.prompt or not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt khali nahi ho sakta.")

    database_result = run_specialist("database", req.prompt)
    backend_result = run_specialist("backend", req.prompt)
    frontend_result = run_specialist("frontend", req.prompt)

    return GenerateResponse(
        feature=req.prompt,
        generated_at=datetime.now().isoformat(),
        model=MODEL_NAME,
        frontend=frontend_result,
        backend=backend_result,
        database=database_result,
    )
