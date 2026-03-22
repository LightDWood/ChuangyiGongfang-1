import uuid
from datetime import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.models import DecisionRecord


class DecisionTrail:
    """Track and record agent decisions"""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    def record(
        self, session_id: str, agent: str, decision: str, reasoning: str
    ) -> DecisionRecord:
        """Record a single decision"""
        record = DecisionRecord(
            id=str(uuid.uuid4()),
            session_id=session_id,
            agent=agent,
            decision=decision,
            reasoning=reasoning,
            created_at=datetime.utcnow(),
        )
        self.db.add(record)
        return record

    async def commit(self) -> None:
        """Commit the recorded decision to database"""
        await self.db.commit()

    async def get_trail(self, session_id: str) -> List[DecisionRecord]:
        """Get all decision records for a session"""
        stmt = select(DecisionRecord).where(
            DecisionRecord.session_id == session_id
        ).order_by(DecisionRecord.created_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_agent_decisions(
        self, session_id: str, agent: str
    ) -> List[DecisionRecord]:
        """Get all decisions made by a specific agent"""
        stmt = select(DecisionRecord).where(
            DecisionRecord.session_id == session_id,
            DecisionRecord.agent == agent,
        ).order_by(DecisionRecord.created_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()