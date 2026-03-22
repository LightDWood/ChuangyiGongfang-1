from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
import json
import asyncio

from .database import init_db, get_db
from .models import Session as DBSession, Message, Artifact
from .agents.lead_agent import LeadAgent
from .api import auth, sessions, artifacts
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(sessions.router, prefix="", tags=["sessions"])
api_router.include_router(artifacts.router, tags=["artifacts"])

app = FastAPI(title="需求收敛智能体 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
async def root():
    return {"message": "需求收敛智能体 API", "version": "0.1.0"}


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/sessions/{session_id}/context")
async def get_session_context(
    session_id: str,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    from .services.auth_service import decode_token

    user_id = decode_token(token)
    if not user_id:
        return {"type": "error", "content": "Unauthorized"}

    result = await db.execute(
        select(DBSession).where(DBSession.id == session_id, DBSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"type": "error", "content": "Session not found"}

    agent = LeadAgent(db)
    summary = await agent.get_context_summary(session_id)
    return summary


@app.post("/api/sessions/{session_id}/resume")
async def resume_session(
    session_id: str,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    from .services.auth_service import decode_token

    user_id = decode_token(token)
    if not user_id:
        return {"type": "error", "content": "Unauthorized"}

    result = await db.execute(
        select(DBSession).where(DBSession.id == session_id, DBSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"type": "error", "content": "Session not found"}

    agent = LeadAgent(db)
    context = await agent.resume_from_checkpoint(session_id, user_id)
    if context:
        return {
            "type": "resumed",
            "state": context.state.value,
            "requirements": context.requirements,
            "step_count": context.step_count,
        }
    return {"type": "no_checkpoint", "content": "没有找到可恢复的检查点"}


from fastapi import Depends
