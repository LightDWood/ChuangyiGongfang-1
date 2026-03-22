"""Quality Assurance Module for Requirement Convergence System"""
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from .evaluator import LLMEvaluator
from .human_intervention import HumanIntervention
from .quality_checks import QualityChecks


class QualityAssurance:
    """Handles LLM self-evaluation and human intervention"""

    def __init__(self, db=None):
        self.evaluation_criteria = {
            "accuracy": "Factual accuracy of statements",
            "completeness": "Coverage of all required content",
            "citation": "Citation accuracy",
            "relevance": "Relevance to user intent"
        }
        self.db = db
        self.evaluator = LLMEvaluator()
        self.human_intervention = HumanIntervention(db)
        self.quality_checks = QualityChecks()
        self._pending_edge_cases: Dict[str, Dict[str, Any]] = {}
        self._confirmation_results: Dict[str, bool] = {}

    async def self_evaluate(self, content: str, content_type: str) -> dict:
        """Self-evaluation before submitting answer"""
        results = {
            "passed": True,
            "scores": {},
            "issues": [],
            "edge_cases": [],
            "timestamp": datetime.utcnow().isoformat(),
            "content_type": content_type
        }

        if content_type == "requirement":
            accuracy_result = await self.evaluator.evaluate_facts(content)
            results["scores"]["accuracy"] = accuracy_result.get("score", 0.0)
            if accuracy_result.get("score", 1.0) < 0.7:
                results["passed"] = False
                results["issues"].append({
                    "criterion": "accuracy",
                    "message": "Factual accuracy below threshold",
                    "details": accuracy_result.get("issues", [])
                })

            completeness_result = await self._evaluate_completeness(content, content_type)
            results["scores"]["completeness"] = completeness_result.get("score", 0.0)
            if completeness_result.get("score", 1.0) < 0.6:
                results["passed"] = False
                results["issues"].append({
                    "criterion": "completeness",
                    "message": "Content completeness below threshold",
                    "details": completeness_result.get("missing", [])
                })

            relevance_result = await self._evaluate_relevance(content, content_type)
            results["scores"]["relevance"] = relevance_result.get("score", 0.0)

        elif content_type == "question":
            clarity_result = await self.quality_checks.check_requirement_clarity(
                {"content": content}
            )
            results["scores"]["clarity"] = clarity_result.get("score", 0.0)
            if clarity_result.get("score", 1.0) < 0.7:
                results["passed"] = False
                results["issues"].append({
                    "criterion": "clarity",
                    "message": "Question clarity below threshold",
                    "details": clarity_result.get("issues", [])
                })

            edge_cases = await self.check_edge_cases({"type": "question", "content": content})
            if edge_cases:
                results["edge_cases"] = edge_cases

        elif content_type == "option":
            quality_result = await self.quality_checks.check_option_quality(
                [content] if isinstance(content, str) else content
            )
            results["scores"]["quality"] = quality_result.get("score", 0.0)
            if quality_result.get("score", 1.0) < 0.6:
                results["passed"] = False
                results["issues"].append({
                    "criterion": "quality",
                    "message": "Option quality below threshold",
                    "details": quality_result.get("issues", [])
                })

        elif content_type == "document":
            citation_result = await self.evaluator.evaluate_citations(content)
            results["scores"]["citation"] = citation_result.get("score", 0.0)

            completeness_result = await self.quality_checks.check_document_completeness(
                content, {}
            )
            results["scores"]["completeness"] = completeness_result.get("score", 0.0)
            if completeness_result.get("score", 1.0) < 0.7:
                results["passed"] = False
                results["issues"].append({
                    "criterion": "completeness",
                    "message": "Document completeness below threshold",
                    "details": completeness_result.get("missing_sections", [])
                })

            edge_cases = await self.check_edge_cases({"type": "document", "content": content})
            if edge_cases:
                results["edge_cases"] = edge_cases

        overall_score = sum(results["scores"].values()) / len(results["scores"]) if results["scores"] else 0.0
        results["overall_score"] = overall_score

        return results

    async def _evaluate_completeness(self, content: str, content_type: str) -> dict:
        """Internal completeness evaluation"""
        required_fields = {
            "requirement": ["core_requirement", "identified_points", "ambiguous_points"],
            "document": ["outline", "sections", "content"]
        }

        required = required_fields.get(content_type, [])
        missing = []

        for field in required:
            if field not in content.lower():
                missing.append(field)

        score = 1.0 - (len(missing) / len(required)) if required else 1.0

        return {
            "score": max(0.0, score),
            "missing": missing
        }

    async def _evaluate_relevance(self, content: str, content_type: str) -> dict:
        """Internal relevance evaluation"""
        irrelevant_keywords = ["unrelated", "off-topic", "irrelevant"]
        has_irrelevant = any(kw in content.lower() for kw in irrelevant_keywords)

        return {
            "score": 0.5 if has_irrelevant else 0.9,
            "relevant": not has_irrelevant
        }

    async def check_edge_cases(self, content: dict) -> List[dict]:
        """Detect and flag edge cases for human review"""
        edge_cases = []
        content_str = content.get("content", "")
        content_type = content.get("type", "")

        if content_type == "question":
            if len(content_str) > 200:
                edge_cases.append({
                    "type": "long_question",
                    "severity": "medium",
                    "description": "Question is unusually long, may confuse users",
                    "original_content": content_str,
                    "suggestion": "Consider breaking into multiple shorter questions"
                })

            if "?" not in content_str:
                edge_cases.append({
                    "type": "no_question_mark",
                    "severity": "high",
                    "description": "Question missing question mark",
                    "original_content": content_str
                })

        if content_type == "document":
            if len(content_str) < 100:
                edge_cases.append({
                    "type": "very_short_document",
                    "severity": "high",
                    "description": "Document is unusually short",
                    "original_content": content_str,
                    "suggestion": "Consider adding more content or sections"
                })

            sensitive_keywords = ["delete", "remove", "drop", "terminate", "cancel"]
            if any(kw in content_str.lower() for kw in sensitive_keywords):
                edge_cases.append({
                    "type": "destructive_operation",
                    "severity": "high",
                    "description": "Content mentions destructive operations",
                    "original_content": content_str,
                    "suggestion": "Verify this is intentional and safe"
                })

        if "应该" in content_str or "必须" in content_str or "一定" in content_str:
            edge_cases.append({
                "type": "absolute_statements",
                "severity": "low",
                "description": "Contains absolute statements that may be too strong",
                "original_content": content_str,
                "suggestion": "Consider using more moderate language"
            })

        uncertain_phrases = ["可能", "也许", "不确定", "或许"]
        if any(phrase in content_str for phrase in uncertain_phrases):
            edge_cases.append({
                "type": "uncertain_statements",
                "severity": "low",
                "description": "Contains uncertain phrases",
                "original_content": content_str
            })

        return edge_cases

    async def wait_for_human_confirmation(self, case: dict) -> bool:
        """Wait for human to confirm edge case handling"""
        confirmation_id = await self.human_intervention.flag_edge_case(
            case_type=case.get("type", "unknown"),
            content={"case": case}
        )

        result = await self.human_intervention.wait_confirmation(
            confirmation_id=confirmation_id,
            timeout=case.get("timeout", 300)
        )

        return result

    async def evaluate_and_wait(
        self,
        content: str,
        content_type: str,
        skip_edge_cases: bool = False
    ) -> dict:
        """Combined evaluation that waits for human intervention if needed"""
        evaluation = await self.self_evaluate(content, content_type)

        if not evaluation["passed"] and not skip_edge_cases:
            for case in evaluation.get("edge_cases", []):
                if case.get("severity") in ["high", "medium"]:
                    confirmed = await self.wait_for_human_confirmation(case)
                    case["human_confirmed"] = confirmed
                    case["confirmation_id"] = self._generate_case_id()

        return evaluation

    def _generate_case_id(self) -> str:
        return f"case_{uuid.uuid4().hex[:8]}"

    async def get_quality_report(self, session_id: str) -> dict:
        """Get quality report for a session"""
        return {
            "session_id": session_id,
            "total_evaluations": len(self._pending_edge_cases),
            "pending_cases": list(self._pending_edge_cases.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def reset(self):
        """Reset QA state"""
        self._pending_edge_cases.clear()
        self._confirmation_results.clear()
