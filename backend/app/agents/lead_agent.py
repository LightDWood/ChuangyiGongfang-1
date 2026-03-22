import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json

from .sub_agents import (
    RequirementUnderstandingAgent,
    QuestionDesignAgent,
    OptionGenerationAgent,
    ResponseProcessingAgent,
    DocumentGenerationAgent,
)
from ..memory import MemoryLayer
from ..quality import QualityAssurance


class ProcessState(Enum):
    IDLE = "idle"
    UNDERSTANDING = "understanding"
    QUESTIONING = "questioning"
    OPTIONS_GENERATING = "options_generating"
    PROCESSING_RESPONSE = "processing_response"
    SYNTHESIZING = "synthesizing"
    GENERATING_DOCUMENT = "generating_document"
    COMPLETED = "completed"


@dataclass
class Task:
    id: str
    agent_name: str
    input_data: Any
    context: Dict[str, Any]
    priority: int = 1
    status: str = "pending"


@dataclass
class Result:
    task_id: str
    agent_name: str
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class ConversationContext:
    session_id: str
    user_id: str
    state: ProcessState = ProcessState.IDLE
    user_input: str = ""
    requirements: List[str] = field(default_factory=list)
    questions: List[Dict[str, Any]] = field(default_factory=list)
    options: Dict[str, List[str]] = field(default_factory=dict)
    selections: Dict[str, Any] = field(default_factory=dict)
    ambiguity_points: List[str] = field(default_factory=list)
    confirmed_requirements: List[str] = field(default_factory=list)
    document: Optional[Dict[str, Any]] = None
    step_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


class LeadAgent:
    def __init__(self, db=None):
        self.agent_id = str(uuid.uuid4())
        self.name = "LeadAgent - Requirement Convergence Orchestrator"
        self.memory = MemoryLayer(db)
        self.db = db
        self.quality_assurance = QualityAssurance(db)

        self.sub_agents = {
            "requirement_understanding": RequirementUnderstandingAgent(),
            "question_design": QuestionDesignAgent(),
            "option_generation": OptionGenerationAgent(),
            "response_processing": ResponseProcessingAgent(),
            "document_generation": DocumentGenerationAgent(),
        }

        self.contexts: Dict[str, ConversationContext] = {}

    def _get_or_create_context(
        self, session_id: str, user_id: str
    ) -> ConversationContext:
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
            )
        return self.contexts[session_id]

    async def process_user_input(
        self, user_input: str, session_id: str, user_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        context = self._get_or_create_context(session_id, user_id)
        context.user_input = user_input
        context.state = ProcessState.UNDERSTANDING
        context.step_count += 1

        await self.memory.save_message(session_id, "user", user_input)
        await self.memory.save_decision_trajectory(
            session_id,
            "user_input_received",
            {"input": user_input, "step": context.step_count},
        )

        yield {
            "type": "thinking",
            "content": "收到您的需求，开始分析...",
            "step": context.step_count,
        }

        understanding_result = await self.understand_requirement(user_input, context)
        yield {
            "type": "thinking",
            "content": self.interleaved_think(1, {"stage": "understanding"}),
            "step": context.step_count,
        }

        if not understanding_result["understood_requirements"]:
            yield {
                "type": "thinking",
                "content": "未能从您的描述中提取明确的需求，请补充更多信息",
                "step": context.step_count,
            }
            return

        context.requirements = understanding_result["understood_requirements"]
        context.ambiguity_points = understanding_result.get("ambiguity_points", [])

        yield {
            "type": "requirement_identified",
            "content": f"我理解了您的 {len(context.requirements)} 个需求",
            "requirements": context.requirements,
            "step": context.step_count,
        }

        if context.ambiguity_points:
            yield {
                "type": "ambiguity_detected",
                "content": "发现以下需要澄清的点",
                "points": context.ambiguity_points,
                "step": context.step_count,
            }

        checkpoint_id = await self.memory.create_checkpoint(
            session_id,
            {
                "state": "understanding_completed",
                "requirements": context.requirements,
                "step": context.step_count,
            },
        )
        yield {
            "type": "checkpoint",
            "content": f"检查点已创建: {checkpoint_id[:8]}",
            "step": context.step_count,
        }

        questions_result = await self.plan_questions(context.requirements, context)
        yield {
            "type": "thinking",
            "content": self.interleaved_think(2, {"stage": "question_planning"}),
            "step": context.step_count,
        }

        context.questions = questions_result.get("questions", [])
        context.state = ProcessState.QUESTIONING

        yield {
            "type": "questions_ready",
            "content": f"我准备了 {len(context.questions)} 个问题来帮助澄清需求",
            "questions": context.questions,
            "step": context.step_count,
        }

        options_result = await self.generate_options(context.questions, context)
        context.options = options_result.get("options_by_question", {})

        yield {
            "type": "thinking",
            "content": self.interleaved_think(3, {"stage": "options_generation"}),
            "step": context.step_count,
        }

        yield {
            "type": "options_ready",
            "content": "选项已生成，请选择或跳过",
            "options": context.options,
            "step": context.step_count,
        }

        await self.memory.save_decision_trajectory(
            session_id,
            "initial_analysis_completed",
            {
                "requirements": context.requirements,
                "questions_count": len(context.questions),
                "options_count": sum(len(o) for o in context.options.values()),
                "step": context.step_count,
            },
        )

        context.state = ProcessState.COMPLETED

        yield {
            "type": "awaiting_selection",
            "content": "请回答上述问题，或直接描述更详细的需求",
            "step": context.step_count,
        }

    async def process_user_selection(
        self, selections: Dict[str, Any], session_id: str, user_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        context = self._get_or_create_context(session_id, user_id)
        context.selections = selections
        context.state = ProcessState.PROCESSING_RESPONSE
        context.step_count += 1

        yield {
            "type": "thinking",
            "content": "正在处理您的选择...",
            "step": context.step_count,
        }

        processing_result = await self._process_response(selections, context)

        context.confirmed_requirements = processing_result.get(
            "confirmed_requirements", context.requirements
        )

        yield {
            "type": "thinking",
            "content": self.interleaved_think(4, {"stage": "response_processing"}),
            "step": context.step_count,
        }

        if processing_result.get("refinement_needed"):
            yield {
                "type": "refinement_needed",
                "content": "以下问题需要进一步明确",
                "points": processing_result["refinement_needed"],
                "step": context.step_count,
            }

        yield {
            "type": "selection_processed",
            "content": processing_result.get("summary", "选择已处理"),
            "step": context.step_count,
        }

        synthesis_result = await self.synthesize_results(
            {
                "requirements": context.requirements,
                "confirmed_requirements": context.confirmed_requirements,
                "ambiguity_points": context.ambiguity_points,
                "selections": context.selections,
            },
            context,
        )

        yield {
            "type": "thinking",
            "content": self.interleaved_think(5, {"stage": "synthesis"}),
            "step": context.step_count,
        }

        document_result = await self.generate_document(synthesis_result, context)

        yield {
            "type": "thinking",
            "content": self.interleaved_think(6, {"stage": "document_generation"}),
            "step": context.step_count,
        }

        context.document = document_result.get("document")
        context.state = ProcessState.GENERATING_DOCUMENT

        artifact = await self.memory.save_generated_document(
            session_id,
            "requirement_specification",
            document_result["document"]["title"],
            json.dumps(document_result["document"], ensure_ascii=False),
        )

        yield {
            "type": "document_generated",
            "content": "需求规格说明书已生成",
            "document": document_result["document"],
            "artifact_id": artifact.id if artifact else None,
            "step": context.step_count,
        }

        await self.memory.save_requirement_summary(
            session_id,
            {
                "requirements": context.requirements,
                "confirmed": context.confirmed_requirements,
                "pending": context.ambiguity_points,
            },
        )

        await self.memory.save_decision_trajectory(
            session_id,
            "document_generated",
            {
                "document_title": document_result["document"]["title"],
                "requirements_count": len(context.requirements),
                "step": context.step_count,
            },
        )

        context.state = ProcessState.COMPLETED

        yield {
            "type": "completed",
            "content": "需求收敛完成！您可以在右侧面板查看生成的需求规格说明书。",
            "step": context.step_count,
        }

    async def understand_requirement(
        self, user_input: str, context: ConversationContext
    ) -> Dict[str, Any]:
        agent = self.sub_agents["requirement_understanding"]
        result = await agent.execute({
            "user_input": user_input,
            "session_id": context.session_id,
        })

        requirement_summary = result.get("requirement_summary", {})
        understood_requirements = requirement_summary.get("core_functions", [])

        if not understood_requirements and requirement_summary.get("project_overview"):
            understood_requirements = [requirement_summary.get("project_overview")]

        return {
            "understood_requirements": understood_requirements,
            "ambiguity_points": result.get("ambiguous_points", []),
            "confidence": result.get("confidence", 0.0),
            "needs_clarification": result.get("needs_clarification", False),
        }

    async def plan_questions(
        self, requirements: List[str], context: ConversationContext
    ) -> Dict[str, Any]:
        agent = self.sub_agents["question_design"]
        result = await agent.execute({
            "project_overview": context.user_input,
            "core_functions": requirements,
            "target_users": "未知",
            "expected_outcomes": [],
            "ambiguous_points": context.ambiguity_points,
            "session_id": context.session_id,
        })
        return result

    async def generate_options(
        self, questions: List[Dict[str, Any]], context: ConversationContext
    ) -> Dict[str, Any]:
        agent = self.sub_agents["option_generation"]
        return await agent.execute(questions)

    async def _process_response(
        self, selections: Dict[str, Any], context: ConversationContext
    ) -> Dict[str, Any]:
        agent = self.sub_agents["response_processing"]
        return await agent.execute(
            selections,
            {
                "session_id": context.session_id,
                "questions": context.questions,
                "requirements": context.requirements,
            },
        )

    async def synthesize_results(
        self, sub_agent_results: Dict[str, Any], context: ConversationContext
    ) -> Dict[str, Any]:
        confirmed = []
        for q_id, selection in context.selections.items():
            if selection and selection not in ["无所谓", "都可以", "暂不需要", "低优先级"]:
                for q in context.questions:
                    if q.get("id") == q_id:
                        confirmed.append(q.get("requirement", ""))

        return {
            "requirements": sub_agent_results.get("requirements", []),
            "confirmed_requirements": confirmed or sub_agent_results.get("confirmed_requirements", []),
            "ambiguity_points": sub_agent_results.get("ambiguity_points", []),
            "selections": sub_agent_results.get("selections", {}),
        }

    async def generate_document(
        self, synthesis_data: Dict[str, Any], context: ConversationContext
    ) -> Dict[str, Any]:
        agent = self.sub_agents["document_generation"]
        result = await agent.execute(
            synthesis_data,
            {
                "session_id": context.session_id,
                "user_input": context.user_input,
            },
        )

        document = result.get("document", {})
        if document:
            qa_result = await self.quality_assurance.self_evaluate(
                json.dumps(document, ensure_ascii=False),
                content_type="document"
            )
            result["quality_assurance"] = qa_result

            if qa_result.get("edge_cases"):
                for case in qa_result["edge_cases"]:
                    if case.get("severity") == "high":
                        context.edge_case_warnings = context.edge_case_warnings or []
                        context.edge_case_warnings.append({
                            "type": "quality_warning",
                            "description": case.get("description"),
                            "case": case,
                        })

        return result

    async def detect_ambiguity(self, context: ConversationContext) -> List[str]:
        ambiguities = []

        if not context.requirements or len(context.requirements) < 2:
            ambiguities.append("需求数量较少，可能需要补充更多需求")

        if not context.questions or len(context.questions) < 3:
            ambiguities.append("问题数量不足，可能存在未覆盖的需求点")

        pending_selections = [
            q_id for q_id, sel in context.selections.items()
            if not sel or sel in ["无所谓", "都可以"]
        ]
        if pending_selections:
            ambiguities.append(f"有 {len(pending_selections)} 个问题尚未明确选择")

        return ambiguities

    async def parallel_delegate(
        self, tasks: List[Task]
    ) -> List[Result]:
        async def execute_task(task: Task) -> Result:
            try:
                agent = self.sub_agents.get(task.agent_name)
                if not agent:
                    return Result(
                        task_id=task.id,
                        agent_name=task.agent_name,
                        success=False,
                        data={},
                        error=f"Unknown agent: {task.agent_name}",
                    )

                data = await agent.execute(task.input_data, task.context)
                return Result(
                    task_id=task.id,
                    agent_name=task.agent_name,
                    success=True,
                    data=data,
                )
            except Exception as e:
                return Result(
                    task_id=task.id,
                    agent_name=task.agent_name,
                    success=False,
                    data={},
                    error=str(e),
                )

        results = await asyncio.gather(*[execute_task(t) for t in tasks])
        return list(results)

    def interleaved_think(self, step: int, context: Dict[str, Any]) -> str:
        thinking_steps = {
            1: "正在理解您的需求描述...",
            2: "正在规划需要澄清的问题...",
            3: "正在生成选项供您选择...",
            4: "正在分析您的选择...",
            5: "正在综合所有信息...",
            6: "正在生成需求规格文档...",
        }
        stage = context.get("stage", "")
        if stage == "understanding":
            return "正在从您的描述中提取关键需求点..."
        elif stage == "question_planning":
            return "正在设计问题以澄清模糊需求..."
        elif stage == "options_generation":
            return "正在为每个问题生成合适的选项..."
        elif stage == "response_processing":
            return "正在处理您的响应并更新理解..."
        elif stage == "synthesis":
            return "正在综合子代理结果形成完整需求..."
        elif stage == "document_generation":
            return "正在将需求转化为规格说明书..."
        return thinking_steps.get(step, "思考中...")

    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.contexts:
            return {"status": "no_context"}

        ctx = self.contexts[session_id]
        return {
            "session_id": session_id,
            "state": ctx.state.value,
            "requirements_count": len(ctx.requirements),
            "questions_count": len(ctx.questions),
            "options_count": sum(len(o) for o in ctx.options.values()),
            "selections_count": len(ctx.selections),
            "step_count": ctx.step_count,
            "has_document": ctx.document is not None,
        }

    async def resume_from_checkpoint(
        self, session_id: str, user_id: str
    ) -> Optional[ConversationContext]:
        checkpoint = await self.memory.get_latest_checkpoint(session_id)
        if not checkpoint:
            return None

        context = self._get_or_create_context(session_id, user_id)
        checkpoint_data = checkpoint.get("data", {})

        context.requirements = checkpoint_data.get("requirements", [])
        context.step_count = checkpoint_data.get("step", 0)
        context.state = ProcessState(checkpoint_data.get("state", "idle"))

        return context
