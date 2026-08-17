import os
import secrets
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, Dict, Any

from agents_engine import engine, AGENT_PERSONAS
from supabase_db import db

app = FastAPI(title="CalShot AI - Multi-Agent HQ")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

APP_PASSWORD = os.getenv("APP_PASSWORD", "CalShot@2026!Sanish")
VALID_SESSIONS = set()

class LoginRequest(BaseModel):
    password: str

class ChatRequest(BaseModel):
    agent_id: str
    message: str

class SettingsRequest(BaseModel):
    gemini_key: str

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "CalShot AI Multi-Agent HQ",
        "supabase_connected": db.client is not None,
        "agents_count": len(AGENT_PERSONAS),
        "ai_active": bool(engine.api_key)
    }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_password": APP_PASSWORD,
        "agents": AGENT_PERSONAS,
        "has_gemini": bool(engine.api_key),
        "supabase_url": db.url
    })

@app.post("/api/login")
async def login(req: LoginRequest, response: Response):
    if req.password == APP_PASSWORD:
        token = secrets.token_hex(24)
        VALID_SESSIONS.add(token)
        response.set_cookie(key="calshot_session", value=token, max_age=86400 * 30, httponly=True)
        return {"success": True, "token": token}
    return JSONResponse(status_code=401, content={"success": False, "error": "Invalid Password"})

@app.post("/api/chat")
async def chat(req: ChatRequest):
    agent_id = req.agent_id or "marketing_lead"
    reply = engine.generate(agent_id, req.message)
    return {"reply": reply, "agent_id": agent_id}

@app.get("/api/campaigns")
async def get_campaigns():
    items = db.get_recent_items(50)
    return {"campaigns": items}

@app.post("/api/settings")
async def update_settings(req: SettingsRequest):
    if req.gemini_key:
        engine.set_key(req.gemini_key.strip())
        return {"status": "ok", "message": "Gemini API key updated"}
    return {"status": "error", "message": "Empty key provided"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
