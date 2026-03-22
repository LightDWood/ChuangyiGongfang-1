import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models.models import Checkpoint, Session


class CheckpointData:
    """Data class representing checkpoint information"""

    def __init__(
        self,
        id: str,
        session_id: str,
        state: dict,
        created_at: datetime,
    ):
        self.id = id
        self.session_id = session_id
        self.state = state
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "state": self.state,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CheckpointSystem:
    """Handle checkpoint creation and recovery"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create(self, session_id: str) -> CheckpointData:
        """Create checkpoint with full state"""
        session_stmt = select(Session).options(
            selectinload(Session.messages),
            selectinload(Session.artifacts),
            selectinload(Session.conversation_messages),
            selectinload(Session.decision_records),
            selectinload(Session.requirement_spec_versions),
        ).where(Session.id == session_id)
        result = await self.db.execute(session_stmt)
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        state = {
            "session_id": session.id,
            "user_id": session.user_id,
            "title": session.title,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in session.messages
            ],
            "artifacts": [
                {
                    "id": art.id,
                    "type": art.type,
                    "title": art.title,
                    "content": art.content,
                    "version": art.version,
                    "created_at": art.created_at.isoformat() if art.created_at else None,
                }
                for art in session.artifacts
            ],
            "conversation_messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None,
                }
                for msg in session.conversation_messages
            ],
            "decision_records": [
                {
                    "id": record.id,
                    "agent": record.agent,
                    "decision": record.decision,
                    "reasoning": record.reasoning,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                }
                for record in session.decision_records
            ],
            "requirement_spec_versions": [
                {
                    "id": spec.id,
                    "version": spec.version,
                    "content": spec.content,
                    "created_at": spec.created_at.isoformat() if spec.created_at else None,
                }
                for spec in session.requirement_spec_versions
            ],
            "checkpoint_created_at": datetime.utcnow().isoformat(),
        }

        checkpoint = Checkpoint(
            id=str(uuid.uuid4()),
            session_id=session_id,
            state=state,
            created_at=datetime.utcnow(),
        )
        self.db.add(checkpoint)
        await self.db.commit()
        await self.db.refresh(checkpoint)

        return CheckpointData(
            id=checkpoint.id,
            session_id=checkpoint.session_id,
            state=checkpoint.state,
            created_at=checkpoint.created_at,
        )

    async def recover(self, checkpoint_id: str) -> dict:
        """Recover state from checkpoint"""
        stmt = select(Checkpoint).where(Checkpoint.id == checkpoint_id)
        result = await self.db.execute(stmt)
        checkpoint = result.scalar_one_or_none()

        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        return checkpoint.state

    async def get_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointData]:
        """Get checkpoint by ID"""
        stmt = select(Checkpoint).where(Checkpoint.id == checkpoint_id)
        result = await self.db.execute(stmt)
        checkpoint = result.scalar_one_or_none()

        if not checkpoint:
            return None

        return CheckpointData(
            id=checkpoint.id,
            session_id=checkpoint.session_id,
            state=checkpoint.state,
            created_at=checkpoint.created_at,
        )

    async def list_checkpoints(self, session_id: str) -> list[CheckpointData]:
        """List all checkpoints for a session"""
        stmt = select(Checkpoint).where(
            Checkpoint.session_id == session_id
        ).order_by(Checkpoint.created_at.desc())
        result = await self.db.execute(stmt)
        checkpoints = result.scalars().all()

        return [
            CheckpointData(
                id=cp.id,
                session_id=cp.session_id,
                state=cp.state,
                created_at=cp.created_at,
            )
            for cp in checkpoints
        ]

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint"""
        stmt = select(Checkpoint).where(Checkpoint.id == checkpoint_id)
        result = await self.db.execute(stmt)
        checkpoint = result.scalar_one_or_none()

        if not checkpoint:
            return False

        await self.db.delete(checkpoint)
        await self.db.commit()
        return True