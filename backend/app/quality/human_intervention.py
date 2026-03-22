"""Human intervention handling"""
import uuid
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum


class CaseStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class HumanIntervention:
    """Handles edge cases requiring human review"""

    def __init__(self, db=None):
        self.db = db
        self._pending_cases: Dict[str, Dict[str, Any]] = {}
        self._confirmation_events: Dict[str, asyncio.Event] = {}
        self._confirmation_results: Dict[str, bool] = {}
        self._callback_registry: Dict[str, Callable] = {}

    async def flag_edge_case(
        self,
        case_type: str,
        content: dict,
        priority: str = "medium",
        metadata: Optional[dict] = None
    ) -> str:
        """Flag edge case and return confirmation_id"""
        confirmation_id = f"conf_{uuid.uuid4().hex[:12]}"

        case = {
            "id": confirmation_id,
            "case_type": case_type,
            "content": content,
            "priority": priority,
            "status": CaseStatus.PENDING.value,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "description": self._generate_case_description(case_type, content)
        }

        self._pending_cases[confirmation_id] = case
        self._confirmation_events[confirmation_id] = asyncio.Event()
        self._confirmation_results[confirmation_id] = False

        await self._notify_human_review(case)

        return confirmation_id

    async def _notify_human_review(self, case: dict):
        """Notify human reviewers of a pending case"""
        notification = {
            "type": "edge_case_review",
            "case_id": case["id"],
            "case_type": case["case_type"],
            "priority": case["priority"],
            "description": case["description"],
            "created_at": case["created_at"]
        }

        if self.db:
            try:
                await self._save_to_database(notification)
            except Exception:
                pass

    async def _save_to_database(self, notification: dict):
        """Save notification to database if available"""
        pass

    async def wait_confirmation(
        self,
        confirmation_id: str,
        timeout: int = 300
    ) -> bool:
        """Wait for human confirmation or timeout"""
        if confirmation_id not in self._confirmation_events:
            return False

        event = self._confirmation_events[confirmation_id]

        try:
            await asyncio.wait_for(
                event.wait(),
                timeout=timeout
            )
            return self._confirmation_results.get(confirmation_id, False)
        except asyncio.TimeoutError:
            if confirmation_id in self._pending_cases:
                self._pending_cases[confirmation_id]["status"] = CaseStatus.TIMEOUT.value
            return False

    async def approve_case(self, confirmation_id: str, notes: Optional[str] = None) -> bool:
        """Approve a pending case"""
        if confirmation_id not in self._pending_cases:
            return False

        self._pending_cases[confirmation_id]["status"] = CaseStatus.APPROVED.value
        self._pending_cases[confirmation_id]["reviewed_at"] = datetime.utcnow().isoformat()
        self._pending_cases[confirmation_id]["review_notes"] = notes
        self._confirmation_results[confirmation_id] = True

        if confirmation_id in self._confirmation_events:
            self._confirmation_events[confirmation_id].set()

        callback = self._callback_registry.get(confirmation_id)
        if callback:
            try:
                await callback(True, notes)
            except Exception:
                pass

        return True

    async def reject_case(
        self,
        confirmation_id: str,
        reason: Optional[str] = None,
        suggested_fix: Optional[str] = None
    ) -> bool:
        """Reject a pending case"""
        if confirmation_id not in self._pending_cases:
            return False

        self._pending_cases[confirmation_id]["status"] = CaseStatus.REJECTED.value
        self._pending_cases[confirmation_id]["reviewed_at"] = datetime.utcnow().isoformat()
        self._pending_cases[confirmation_id]["rejection_reason"] = reason
        self._pending_cases[confirmation_id]["suggested_fix"] = suggested_fix
        self._confirmation_results[confirmation_id] = False

        if confirmation_id in self._confirmation_events:
            self._confirmation_events[confirmation_id].set()

        callback = self._callback_registry.get(confirmation_id)
        if callback:
            try:
                await callback(False, reason)
            except Exception:
                pass

        return True

    async def get_pending_cases(
        self,
        priority: Optional[str] = None,
        case_type: Optional[str] = None
    ) -> list:
        """Get all pending cases, optionally filtered"""
        cases = [
            case for case in self._pending_cases.values()
            if case["status"] == CaseStatus.PENDING.value
        ]

        if priority:
            cases = [c for c in cases if c.get("priority") == priority]

        if case_type:
            cases = [c for c in cases if c.get("case_type") == case_type]

        return sorted(cases, key=lambda x: x["created_at"])

    async def get_case(self, confirmation_id: str) -> Optional[dict]:
        """Get details of a specific case"""
        return self._pending_cases.get(confirmation_id)

    async def register_callback(
        self,
        confirmation_id: str,
        callback: Callable[[bool, Optional[str]], Any]
    ):
        """Register a callback to be called when case is resolved"""
        self._callback_registry[confirmation_id] = callback

    def _generate_case_description(self, case_type: str, content: dict) -> str:
        """Generate human-readable description for a case"""
        descriptions = {
            "long_question": "问题过长，可能需要拆分",
            "no_question_mark": "问题缺少问号",
            "very_short_document": "文档内容过短",
            "destructive_operation": "涉及危险操作",
            "absolute_statements": "包含绝对性陈述",
            "uncertain_statements": "包含不确定性陈述",
            "low_confidence": "置信度低于阈值",
            "ambiguous_content": "内容存在歧义"
        }

        base_description = descriptions.get(case_type, f"未知类型边缘案例: {case_type}")

        if isinstance(content, dict):
            original = content.get("original_content", "")
            if original and len(original) > 100:
                original = original[:100] + "..."
            return f"{base_description} - {original}"

        return base_description

    async def clear_resolved_cases(self, older_than_hours: int = 24) -> int:
        """Clear resolved cases older than specified hours"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)

        to_remove = []
        for case_id, case in self._pending_cases.items():
            if case["status"] != CaseStatus.PENDING.value:
                try:
                    created = datetime.fromisoformat(case["created_at"])
                    if created < cutoff:
                        to_remove.append(case_id)
                except Exception:
                    pass

        for case_id in to_remove:
            del self._pending_cases[case_id]
            self._confirmation_events.pop(case_id, None)
            self._confirmation_results.pop(case_id, None)
            self._callback_registry.pop(case_id, None)

        return len(to_remove)

    async def get_statistics(self) -> dict:
        """Get statistics about human interventions"""
        total = len(self._pending_cases)
        pending = sum(1 for c in self._pending_cases.values() if c["status"] == CaseStatus.PENDING.value)
        approved = sum(1 for c in self._pending_cases.values() if c["status"] == CaseStatus.APPROVED.value)
        rejected = sum(1 for c in self._pending_cases.values() if c["status"] == CaseStatus.REJECTED.value)
        timeout = sum(1 for c in self._pending_cases.values() if c["status"] == CaseStatus.TIMEOUT.value)

        return {
            "total_cases": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "timeout": timeout,
            "approval_rate": approved / (approved + rejected) if (approved + rejected) > 0 else 0.0
        }
