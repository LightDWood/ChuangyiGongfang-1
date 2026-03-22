from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
import json
import asyncio

from ..database import get_db
from ..models import Session as DBSession, User, Message, Artifact
from ..agents.lead_agent import LeadAgent
from .auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    user_id: str


class CreateSessionRequest(BaseModel):
    title: str = "新会话"


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    created_at: datetime


class MessageCreate(BaseModel):
    content: str


async def _get_session_with_permission(db: AsyncSession, session_id: str, user_id: str) -> Optional[DBSession]:
    result = await db.execute(
        select(DBSession).where(DBSession.id == session_id, DBSession.user_id == user_id)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=SessionResponse)
async def create_session(
    request: CreateSessionRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = DBSession(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=request.title if request else "新会话",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        user_id=session.user_id,
    )


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DBSession)
        .where(DBSession.user_id == current_user.id)
        .order_by(DBSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        SessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            user_id=s.user_id,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_session_with_permission(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        user_id=session.user_id,
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_session_with_permission(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}


@router.get("/{session_id}/artifacts", response_model=List[dict])
async def get_session_artifacts(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_session_with_permission(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from ..models import Artifact
    result = await db.execute(
        select(Artifact)
        .where(Artifact.session_id == session_id, Artifact.user_id == current_user.id)
        .order_by(Artifact.updated_at.desc())
    )
    artifacts = result.scalars().all()
    return [
        {
            "id": a.id,
            "session_id": a.session_id,
            "title": a.name,
            "type": a.artifact_type,
            "content": "",
            "version": a.current_version,
            "created_at": a.created_at.isoformat(),
            "updated_at": a.updated_at.isoformat(),
        }
        for a in artifacts
    ]


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_session_with_permission(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_session_with_permission(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=message.content,
    )
    session.updated_at = datetime.utcnow()
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    user_id = current_user.id
    agent = LeadAgent(db)
    agent_response_content = ""

    try:
        async for chunk in agent.process_user_input(message.content, session_id, current_user.id):
            if chunk.get("type") == "document_generated":
                artifact_data = chunk.get("document")
                if artifact_data:
                    artifact = Artifact(
                        id=str(uuid.uuid4()),
                        session_id=session_id,
                        user_id=user_id,
                        artifact_type="requirement_specification",
                        name=artifact_data.get("title", "需求规格说明书"),
                        current_version=1,
                    )
                    db.add(artifact)
                    await db.commit()
    except Exception as e:
        print(f"Agent processing error: {e}")
        import traceback
        traceback.print_exc()

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id, Message.role == "user")
        .order_by(Message.created_at.desc())
    )
    all_user_messages = result.scalars().all()
    if len(all_user_messages) == 1:
        session.title = message.content[:50] + ("..." if len(message.content) > 50 else "")
        await db.commit()

    agent_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="agent",
        content="处理完成",
    )
    db.add(agent_message)
    await db.commit()
    await db.refresh(agent_message)

    return MessageResponse(
        id=agent_message.id,
        session_id=agent_message.session_id,
        role=agent_message.role,
        content=agent_message.content,
        created_at=agent_message.created_at,
    )


@router.get("/{session_id}/stream")
async def stream_message(
    session_id: str,
    content: str,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    from ..services.auth_service import decode_token

    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    result = await db.execute(
        select(DBSession).where(DBSession.id == session_id, DBSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="user",
        content=content,
    )
    session.updated_at = datetime.utcnow()
    db.add(user_message)
    await db.commit()

    async def event_generator():
        pending_artifacts = []
        agent = LeadAgent(db)

        async for chunk in agent.process_user_input(content, session_id, user_id):
            if chunk.get("type") == "document_generated":
                artifact_data = chunk.get("document")
                if artifact_data:
                    pending_artifacts.append({
                        "data": artifact_data,
                        "chunk": chunk,
                    })
                    yield f"event: artifact\ndata: {json.dumps({'content': artifact_data.get('title', '需求规格说明书'), 'artifact': artifact_data}, ensure_ascii=False)}\n\n"
            elif chunk.get("type") == "error":
                yield f"event: error\ndata: {json.dumps({'content': chunk.get('message', '未知错误')}, ensure_ascii=False)}\n\n"
            else:
                yield f"event: token\ndata: {json.dumps({'content': chunk.get('content', '')}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.01)

        for item in pending_artifacts:
            artifact = Artifact(
                id=str(uuid.uuid4()),
                session_id=session_id,
                user_id=user_id,
                artifact_type="requirement_specification",
                name=item["data"].get("title", "需求规格说明书"),
                current_version=1,
            )
            db.add(artifact)
            await db.commit()
            item["chunk"]["artifact_id"] = artifact.id

        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id, Message.role == "user")
            .order_by(Message.created_at.desc())
        )
        all_user_messages = result.scalars().all()
        if len(all_user_messages) == 1:
            session.title = content[:50] + ("..." if len(content) > 50 else "")
            session.updated_at = datetime.utcnow()
            await db.commit()

        yield f"event: done\ndata: \n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
