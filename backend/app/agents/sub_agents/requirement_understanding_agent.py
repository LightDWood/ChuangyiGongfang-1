import re
from typing import Dict, List, Optional
from .template import QUALITY_CHECKLIST, INTERLEAVED_THINKING_PROMPT


class RequirementUnderstandingAgent:
    """Sub-agent: Understand user requirement and restate it"""

    def __init__(self):
        self.name = "RequirementUnderstandingAgent"
        self.context_window = []

    async def execute(self, context: dict) -> dict:
        self.context_window = context.get("conversation_history", [])
        user_input = context.get("user_input", "")
        session_id = context.get("session_id", "")

        thought = await self.think(context)
        understanding = await self._understand_requirement(user_input, context)

        thought = await self.think_after_understanding(understanding)
        requirement_summary = await self._restate_requirement(understanding, context)

        thought = await self.think_after_restatement(requirement_summary)
        is_valid = await self._validate_output(requirement_summary)

        if not is_valid:
            requirement_summary = await self._refine_requirement(requirement_summary, context)

        return {
            "agent": self.name,
            "requirement_summary": requirement_summary,
            "identified_points": understanding.get("identified_points", []),
            "ambiguous_points": understanding.get("ambiguous_points", []),
            "confidence": understanding.get("confidence", 0.0),
            "needs_clarification": len(understanding.get("ambiguous_points", [])) > 0,
        }

    async def think(self, context: dict) -> str:
        prompt = f"""你是一个需求理解专家。你的任务是理解用户的原始需求，并对其进行结构化重述。

{INTERLEAVED_THINKING_PROMPT}

当前对话上下文：
{self._format_context(context)}

请先思考：
1. 用户的核心需求是什么？
2. 需求中有哪些模糊或不确定的地方？
3. 我需要提取哪些关键信息？

然后执行理解任务。
"""
        return prompt

    async def think_after_understanding(self, understanding: dict) -> str:
        return f"""自我反思 - 理解阶段完成

理解结果检查：
- 核心需求提取：{'✓' if understanding.get('core_requirement') else '✗'}
- 关键信息点：{len(understanding.get('identified_points', []))} 个
- 模糊点识别：{len(understanding.get('ambiguous_points', []))} 个
- 理解置信度：{understanding.get('confidence', 0):.0%}

接下来需要将理解的需求进行清晰的重述，确保用户能够确认我的理解是否正确。
"""

    async def think_after_restatement(self, requirement_summary: dict) -> str:
        return f"""自我反思 - 重述阶段完成

重述结果检查：
- 项目概述：{'✓' if requirement_summary.get('project_overview') else '✗'}
- 核心功能：{len(requirement_summary.get('core_functions', []))} 项
- 用户群体：{'✓' if requirement_summary.get('target_users') else '✗'}
- 成功标准：{len(requirement_summary.get('success_criteria', []))} 项

现在需要验证输出质量，确保重述清晰准确。
"""

    async def _understand_requirement(self, user_input: str, context: dict) -> dict:
        prompt = f"""你是一个专业的需求分析专家。请分析以下用户需求，提取关键信息并识别模糊点。

原始用户输入：
{user_input}

对话历史：
{self._format_history(context.get('conversation_history', []))}

请以JSON格式输出分析结果：
{{
    "core_requirement": "一句话描述核心需求",
    "identified_points": [
        {{
            "type": "功能|技术|业务|约束",
            "content": "具体描述",
            "priority": "高|中|低",
            "keywords": ["关键词1", "关键词2"]
        }}
    ],
    "ambiguous_points": [
        {{
            "point": "模糊点描述",
            "question": "可以用来澄清的问题",
            "importance": "高|中|低"
        }}
    ],
    "confidence": 0.0-1.0之间的置信度数值,
    "missing_info": ["缺少的关键信息列表"]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        return self._parse_json_response(result)

    async def _restate_requirement(self, understanding: dict, context: dict) -> dict:
        prompt = f"""基于以下需求分析结果，请生成结构化的需求重述。

分析结果：
{self._format_dict(understanding)}

对话上下文：
{self._format_context(context)}

请生成以下格式的需求重述：

1. 项目概述：一段话概括项目
2. 核心功能列表：提取出的核心功能
3. 目标用户：系统的主要使用者
4. 预期成果：项目交付的成果
5. 成功标准：如何判断项目成功
6. 已知约束：已明确的项目限制

以JSON格式输出：
{{
    "project_overview": "项目概述描述",
    "core_functions": ["功能1", "功能2", ...],
    "target_users": "目标用户描述",
    "expected_outcomes": ["成果1", "成果2", ...],
    "success_criteria": ["标准1", "标准2", ...],
    "known_constraints": ["约束1", "约束2", ...]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        return self._parse_json_response(result)

    async def _validate_output(self, requirement_summary: dict) -> bool:
        checklist = QUALITY_CHECKLIST["requirement_understanding"]
        for item in checklist:
            if not self._check_quality_item(requirement_summary, item):
                return False
        return True

    async def _refine_requirement(self, requirement_summary: dict, context: dict) -> dict:
        prompt = f"""请改进以下需求重述，使其更加清晰和完整。

当前需求重述：
{self._format_dict(requirement_summary)}

请检查并改进：
1. 是否有遗漏的重要信息？
2. 描述是否清晰易懂？
3. 结构是否合理？

请以JSON格式输出改进后的版本。
"""
        result = await self._call_llm(prompt)
        refined = self._parse_json_response(result)
        return refined if refined else requirement_summary

    async def _call_llm(self, prompt: str) -> str:
        from ..llm_client import get_llm_client
        client = get_llm_client()
        response = await client.generate(prompt)
        return response

    def _parse_json_response(self, response: str) -> dict:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                return json.loads(json_match.group())
        except Exception:
            pass
        return {}

    def _format_context(self, context: dict) -> str:
        lines = []
        for key, value in context.items():
            if key != "conversation_history":
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "无额外上下文"

    def _format_history(self, history: list) -> str:
        if not history:
            return "无历史对话"
        return "\n".join([
            f"[{msg.get('role', 'unknown')}]: {msg.get('content', '')}"
            for msg in history[-5:]
        ])

    def _format_dict(self, d: dict) -> str:
        return "\n".join([f"- {k}: {v}" for k, v in d.items()])

    def _check_quality_item(self, data: dict, quality_item: str) -> bool:
        keywords = {
            "核心需求": ["core_requirement", "project_overview"],
            "模糊点": ["ambiguous_points"],
            "上下文": ["context", "conversation_history"],
            "清晰易懂": ["project_overview", "core_functions"],
        }
        for key in keywords.get(quality_item.split("是否")[1], []):
            if key in data and data[key]:
                return True
        return True
