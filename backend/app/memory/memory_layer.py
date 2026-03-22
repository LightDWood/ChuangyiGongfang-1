import uuid
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models.models import (
    ConversationMessage,
    DecisionRecord,
    Checkpoint,
    RequirementSpecVersion,
    Session,
    Artifact,
)


class MemoryLayer:
    """Memory Layer for storing conversation history, decisions, and state"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def save_message(self, session_id: str, role: str, content: str) -> ConversationMessage:
        """Save message to conversation history"""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            created_at=datetime.utcnow(),
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_conversation_history(self, session_id: str) -> List[dict]:
        """Get full conversation history for a session"""
        stmt = select(ConversationMessage).where(
            ConversationMessage.session_id == session_id
        ).order_by(ConversationMessage.created_at)
        result = await self.db.execute(stmt)
        messages = result.scalars().all()
        return [
            {
                "id": msg.id,
                "session_id": msg.session_id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ]

    async def save_decision(self, session_id: str, decision: dict) -> DecisionRecord:
        """Save Lead Agent decision trajectory"""
        record = DecisionRecord(
            id=str(uuid.uuid4()),
            session_id=session_id,
            agent=decision.get("agent", "lead_agent"),
            decision=decision.get("decision", ""),
            reasoning=decision.get("reasoning", ""),
            created_at=datetime.utcnow(),
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def save_decision_trajectory(
        self, session_id: str, decision_type: str, decision_data: dict
    ) -> DecisionRecord:
        """Save a decision trajectory entry"""
        record = DecisionRecord(
            id=str(uuid.uuid4()),
            session_id=session_id,
            agent="lead_agent",
            decision=decision_type,
            reasoning=str(decision_data),
            created_at=datetime.utcnow(),
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def get_decision_trail(self, session_id: str) -> List[dict]:
        """Get all decisions made in a session"""
        stmt = select(DecisionRecord).where(
            DecisionRecord.session_id == session_id
        ).order_by(DecisionRecord.created_at)
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "id": record.id,
                "session_id": record.session_id,
                "agent": record.agent,
                "decision": record.decision,
                "reasoning": record.reasoning,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            }
            for record in records
        ]

    async def create_checkpoint(self, session_id: str, metadata: dict = None) -> str:
        """Create a checkpoint for current state, return checkpoint_id"""
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
            "metadata": metadata or {},
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
        return checkpoint.id

    async def restore_from_checkpoint(self, checkpoint_id: str) -> dict:
        """Restore session state from checkpoint"""
        stmt = select(Checkpoint).where(Checkpoint.id == checkpoint_id)
        result = await self.db.execute(stmt)
        checkpoint = result.scalar_one_or_none()

        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        return checkpoint.state

    async def save_requirement_spec(
        self, session_id: str, content: str, version: int
    ) -> RequirementSpecVersion:
        """Save a version of the generated requirement specification"""
        spec_version = RequirementSpecVersion(
            id=str(uuid.uuid4()),
            session_id=session_id,
            version=version,
            content=content,
            created_at=datetime.utcnow(),
        )
        self.db.add(spec_version)
        await self.db.commit()
        await self.db.refresh(spec_version)
        return spec_version

    async def get_requirement_spec_versions(self, session_id: str) -> List[dict]:
        """Get all versions of requirement spec for a session"""
        stmt = select(RequirementSpecVersion).where(
            RequirementSpecVersion.session_id == session_id
        ).order_by(RequirementSpecVersion.version)
        result = await self.db.execute(stmt)
        versions = result.scalars().all()
        return [
            {
                "id": spec.id,
                "session_id": spec.session_id,
                "version": spec.version,
                "content": spec.content,
                "created_at": spec.created_at.isoformat() if spec.created_at else None,
            }
            for spec in versions
        ]

    async def get_latest_checkpoint(self, session_id: str) -> dict:
        """Get the latest checkpoint for a session"""
        stmt = select(Checkpoint).where(
            Checkpoint.session_id == session_id
        ).order_by(Checkpoint.created_at.desc()).limit(1)
        result = await self.db.execute(stmt)
        checkpoint = result.scalar_one_or_none()
        return checkpoint.state if checkpoint else None

    async def save_generated_document(
        self, session_id: str, doc_type: str, title: str, content: str
    ) -> Artifact:
        """Save a generated artifact/document"""
        artifact = Artifact(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id="",  # Will be set by caller
            artifact_type=doc_type,
            name=title,
            current_version=1,
        )
        self.db.add(artifact)
        await self.db.commit()
        await self.db.refresh(artifact)
        return artifact

    async def save_requirement_summary(
        self, session_id: str, summary: dict
    ) -> ConversationMessage:
        """Save the final requirement summary"""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="system",
            content=str(summary),
            created_at=datetime.utcnow(),
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message