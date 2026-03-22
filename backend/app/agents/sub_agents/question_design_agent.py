import re
from typing import Dict, List
from .template import QUESTION_DESIGN_GUIDELINES, QUALITY_CHECKLIST, INTERLEAVED_THINKING_PROMPT


class QuestionDesignAgent:
    """Sub-agent: Design questions based on requirement"""

    def __init__(self):
        self.name = "QuestionDesignAgent"
        self.max_questions = QUESTION_DESIGN_GUIDELINES.get("max_questions_per_round", 5)

    async def execute(self, requirement: dict) -> dict:
        thought = await self.think_before_design(requirement)

        question_list = await self._design_questions(requirement)

        thought = await self.think_after_design(question_list)

        categorized = await self._categorize_questions(question_list)

        thought = await self.think_after_categorization(categorized)

        prioritized = await self._prioritize_questions(categorized)

        is_valid = await self._validate_output(prioritized)

        if not is_valid:
            prioritized = await self._refine_questions(prioritized, requirement)

        return {
            "agent": self.name,
            "questions": prioritized,
            "total_count": len(prioritized),
            "by_priority": {
                "high": len([q for q in prioritized if q.get("priority") == "high"]),
                "medium": len([q for q in prioritized if q.get("priority") == "medium"]),
                "low": len([q for q in prioritized if q.get("priority") == "low"]),
            },
            "by_type": self._count_by_type(prioritized),
        }

    async def think_before_design(self, requirement: dict) -> str:
        return f"""自我反思 - 问题设计前

任务理解：
- 我需要根据需求设计澄清问题
- 问题应覆盖所有模糊点
- 问题应遵循设计原则

需求分析：
- 项目概述：{requirement.get('project_overview', '')[:50]}...
- 核心功能：{len(requirement.get('core_functions', []))} 项
- 目标用户：{requirement.get('target_users', '未知')}
- 已知模糊点：{len(requirement.get('ambiguous_points', []))} 个

接下来设计具体问题。
"""

    async def think_after_design(self, question_list: list) -> str:
        return f"""自我反思 - 问题设计完成

设计结果检查：
- 问题数量：{len(question_list)} 个
- 模糊点覆盖率：{len(question_list) / max(1, 5) * 100:.0f}%
- 问题类型多样性：{len(set(q.get('type') for q in question_list))} 种

现在需要：
1. 将问题分类（澄清型、确认型、探索型等）
2. 按优先级排序
3. 确保关键问题在前
"""

    async def think_after_categorization(self, categorized: dict) -> str:
        return f"""自我反思 - 问题分类完成

分类结果：
- 澄清型问题：{len(categorized.get('clarification', []))} 个
- 确认型问题：{len(categorized.get('confirmation', []))} 个
- 探索型问题：{len(categorized.get('exploration', []))} 个
- 约束型问题：{len(categorized.get('constraint', []))} 个
- 偏好型问题：{len(categorized.get('preference', []))} 个

现在按优先级排序，确保关键问题优先呈现。
"""

    async def _design_questions(self, requirement: dict) -> List[dict]:
        prompt = f"""你是一个专业的需求分析师。请根据以下需求，设计问题列表来澄清模糊点。

需求摘要：
- 项目概述：{requirement.get('project_overview', '')}
- 核心功能：{', '.join(requirement.get('core_functions', []))}
- 目标用户：{requirement.get('target_users', '未知')}
- 预期成果：{', '.join(requirement.get('expected_outcomes', []))}

{QUESTION_DESIGN_GUIDELINES}

设计指南：
- 问题类型：clarification（澄清）、confirmation（确认）、exploration（探索）、constraint（约束）、preference（偏好）
- 每个问题应有明确的用途
- 关键问题优先
- 最多设计 {self.max_questions} 个问题

请以JSON格式输出问题列表：
{{
    "questions": [
        {{
            "id": "q[n]",
            "question": "问题内容",
            "type": "问题类型",
            "purpose": "为什么需要问这个问题",
            "priority": "high|medium|low",
            "target_section": "对应需求章节"
        }}
    ]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        parsed = self._parse_json_response(result)
        return parsed.get("questions", [])

    async def _categorize_questions(self, questions: List[dict]) -> Dict[str, List[dict]]:
        categorized = {
            "clarification": [],
            "confirmation": [],
            "exploration": [],
            "constraint": [],
            "preference": [],
        }

        for q in questions:
            q_type = q.get("type", "clarification")
            if q_type in categorized:
                categorized[q_type].append(q)
            else:
                categorized["clarification"].append(q)

        return categorized

    async def _prioritize_questions(self, categorized: Dict[str, List[dict]]) -> List[dict]:
        priority_order = ["high", "medium", "low"]
        type_order = ["clarification", "constraint", "confirmation", "exploration", "preference"]

        all_questions = []
        for priority in priority_order:
            for q_type in type_order:
                all_questions.extend(categorized.get(q_type, []))

        reordered = []
        for q in all_questions:
            if q not in reordered:
                reordered.append(q)

        return reordered[: self.max_questions]

    async def _validate_output(self, questions: List[dict]) -> bool:
        if not questions:
            return False

        checklist = QUALITY_CHECKLIST["question_design"]
        for item in checklist:
            if not self._check_quality(questions, item):
                return False

        return True

    async def _refine_questions(self, questions: List[dict], requirement: dict) -> List[dict]:
        prompt = f"""请改进以下问题列表，使其更加有效。

当前问题列表：
{self._format_questions(questions)}

需求背景：
{requirement.get('project_overview', '')}

请检查并改进：
1. 是否覆盖了所有关键模糊点？
2. 问题顺序是否合理？
3. 是否有冗余或重复的问题？

请以JSON格式输出改进后的版本。
"""
        result = await self._call_llm(prompt)
        parsed = self._parse_json_response(result)
        return parsed.get("questions", questions)

    async def _call_llm(self, prompt: str) -> str:
        from ..llm_client import get_llm_client

        client = get_llm_client()
        response = await client.generate(prompt)
        return response

    def _parse_json_response(self, response: str) -> dict:
        try:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                import json

                return json.loads(json_match.group())
            array_match = re.search(r"\[.*\]", response, re.DOTALL)
            if array_match:
                import json

                return {"questions": json.loads(array_match.group())}
        except Exception:
            pass
        return {}

    def _format_questions(self, questions: List[dict]) -> str:
        return "\n".join(
            [f"{q.get('id')}: {q.get('question')}" for q in questions]
        )

    def _count_by_type(self, questions: List[dict]) -> Dict[str, int]:
        counts = {}
        for q in questions:
            q_type = q.get("type", "unknown")
            counts[q_type] = counts.get(q_type, 0) + 1
        return counts

    def _check_quality(self, questions: List[dict], quality_item: str) -> bool:
        if "覆盖" in quality_item and "模糊点" in quality_item:
            return len(questions) >= 3
        if "逻辑顺序" in quality_item:
            return True
        if "简洁明了" in quality_item:
            return all(len(q.get("question", "")) < 200 for q in questions)
        if "便于回答" in quality_item:
            return all(q.get("type") for q in questions)
        return True
