import re
from typing import Dict, List, Optional
from .template import QUALITY_CHECKLIST, INTERLEAVED_THINKING_PROMPT


class ResponseProcessingAgent:
    """Sub-agent: Process user's response to options"""

    def __init__(self):
        self.name = "ResponseProcessingAgent"
        self.clarity_threshold = 0.7

    async def execute(self, selection: dict, context: dict) -> dict:
        thought = await self.think_before_processing(selection, context)

        parsed_selections = await self._parse_selections(selection, context)

        thought = await self.think_after_parsing(parsed_selections)

        updated_requirement = await self._update_requirement(
            parsed_selections, context
        )

        thought = await self.think_after_update(updated_requirement)

        clarity_result = await self._evaluate_clarity(
            updated_requirement, context
        )

        thought = await self.think_after_clarity(clarity_result)

        next_action = await self._determine_next_action(
            clarity_result, updated_requirement, context
        )

        return {
            "agent": self.name,
            "parsed_selections": parsed_selections,
            "updated_requirement": updated_requirement,
            "clarity_assessment": clarity_result,
            "next_action": next_action,
            "confidence": clarity_result.get("overall_clarity", 0.0),
        }

    async def think_before_processing(self, selection: dict, context: dict) -> str:
        selections_count = len(selection.get("selections", {})) if isinstance(selection, dict) else 0

        return f"""自我反思 - 响应处理前

任务理解：
- 我需要处理用户对问题的选择
- 理解上下文和当前需求状态
- 判断是否需要继续澄清或可以生成文档

当前状态：
- 选择数量：{selections_count} 个
- 上下文完整性：{self._assess_context_completeness(context)}
- 已有澄清轮次：{context.get('clarification_rounds', 0)}

接下来解析用户选择。
"""

    async def think_after_parsing(self, parsed_selections: dict) -> str:
        return f"""自我反思 - 解析完成

解析结果：
- 成功解析的选择：{len(parsed_selections.get('successful', []))} 个
- 解析失败的选择：{len(parsed_selections.get('failed', []))} 个
- 关键选择：{len(parsed_selections.get('key_selections', []))} 个

现在将选择结果整合到需求中。
"""

    async def think_after_update(self, updated_requirement: dict) -> str:
        key_updates = [
            k for k in updated_requirement.keys()
            if "_updated" in k or k in ["core_functions", "target_users", "constraints"]
        ]

        return f"""自我反思 - 需求更新完成

更新内容：
- 更新的关键字段：{', '.join(key_updates) if key_updates else '无'}
- 核心功能数：{len(updated_requirement.get('core_functions', []))}
- 约束条件数：{len(updated_requirement.get('constraints', []))}
- 目标用户：{updated_requirement.get('target_users', '未指定')}

现在评估需求的清晰度。
"""

    async def think_after_clarity(self, clarity_result: dict) -> str:
        return f"""自我反思 - 清晰度评估完成

评估结果：
- 总体清晰度：{clarity_result.get('overall_clarity', 0):.0%}
- 模糊点数量：{len(clarity_result.get('remaining_ambiguous', []))}
- 关键模糊点：{', '.join(clarity_result.get('critical_ambiguous', [])[:3]) if clarity_result.get('critical_ambiguous') else '无'}

根据评估结果决定下一步行动。
"""

    async def _parse_selections(self, selection: dict, context: dict) -> dict:
        prompt = f"""你是一个需求理解专家。请解析用户的选择结果，理解每个选择的含义。

用户选择：
{self._format_selection(selection)}

选项上下文：
{self._format_options_context(context)}

请分析每个选择：
1. 用户选择了哪个选项？
2. 这个选择对需求有什么影响？
3. 是否需要更新某些需求项？

请以JSON格式输出解析结果：
{{
    "successful": [
        {{
            "question_id": "问题ID",
            "selected_option": {{"id": "选项ID", "label": "选项标签", "description": "选项描述"}},
            "requirement_impact": "对需求的影响描述",
            "affected_fields": ["受影响的字段列表"]
        }}
    ],
    "failed": ["解析失败的选项ID列表"],
    "key_selections": ["关键选择的问题ID列表"]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        return self._parse_json_response(result)

    async def _update_requirement(
        self, parsed_selections: dict, context: dict
    ) -> dict:
        current_requirement = context.get("current_requirement", {})

        prompt = f"""请根据用户的选择更新需求规格。

当前需求：
{self._format_requirement(current_requirement)}

用户选择解析：
{self._format_parsed_selections(parsed_selections)}

请更新以下内容：
1. 根据选择添加或修改功能
2. 更新约束条件
3. 明确目标用户
4. 调整成功标准

请以JSON格式输出更新后的需求：
{{
    "project_overview": "更新后的项目概述",
    "core_functions": ["更新的核心功能列表"],
    "target_users": "更新后的目标用户",
    "expected_outcomes": ["更新后的预期成果"],
    "success_criteria": ["更新后的成功标准"],
    "constraints": ["更新后的约束条件"],
    "ambiguous_points_resolved": ["已解决的模糊点"],
    "ambiguous_points_remaining": ["仍存在的模糊点"]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        updated = self._parse_json_response(result)

        for key in ["ambiguous_points_resolved", "ambiguous_points_remaining"]:
            if key not in updated:
                updated[key] = []

        return updated

    async def _evaluate_clarity(
        self, requirement: dict, context: dict
    ) -> dict:
        prompt = f"""请评估当前需求的清晰程度。

需求内容：
{self._format_requirement(requirement)}

评估维度：
1. 功能完整性：核心功能是否都已明确？
2. 约束清晰度：约束条件是否明确？
3. 目标明确性：目标用户和预期成果是否清晰？
4. 验收可行性：成功标准是否可测试？

请以JSON格式输出评估结果：
{{
    "overall_clarity": 0.0-1.0之间的数值,
    "dimension_scores": {{
        "functionality": 0.0-1.0,
        "constraints": 0.0-1.0,
        "clarity": 0.0-1.0,
        "acceptance": 0.0-1.0
    }},
    "remaining_ambiguous": ["仍存在模糊的点"],
    "critical_ambiguous": ["关键的模糊点（影响文档生成）"]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        clarity = self._parse_json_response(result)

        if not clarity.get("overall_clarity"):
            clarity["overall_clarity"] = self.clarity_threshold

        return clarity

    async def _determine_next_action(
        self,
        clarity_result: dict,
        requirement: dict,
        context: dict,
    ) -> dict:
        clarity = clarity_result.get("overall_clarity", 0)
        critical_ambiguous = clarity_result.get("critical_ambiguous", [])
        rounds = context.get("clarification_rounds", 0)

        if clarity >= self.clarity_threshold and not critical_ambiguous:
            return {
                "action": "generate_document",
                "reason": f"需求清晰度达到 {clarity:.0%}，可以生成文档",
                "confidence": clarity,
            }

        if rounds >= 3:
            return {
                "action": "generate_document",
                "reason": "已达到最大澄清轮次，使用当前信息生成文档",
                "confidence": clarity,
            }

        return {
            "action": "generate_questions",
            "reason": f"仍存在 {len(critical_ambiguous)} 个关键模糊点，需要继续澄清",
            "critical_points": critical_ambiguous,
            "confidence": clarity,
        }

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

                return {"result": json.loads(array_match.group())}
        except Exception:
            pass
        return {}

    def _format_selection(self, selection: dict) -> str:
        if isinstance(selection, dict):
            selections = selection.get("selections", selection)
            return "\n".join(
                [f"- {k}: {v}" for k, v in selections.items()]
            )
        return str(selection)

    def _format_options_context(self, context: dict) -> str:
        options_by_question = context.get("options_by_question", {})
        lines = []
        for q_id, data in options_by_question.items():
            lines.append(f"问题 {q_id}:")
            for opt in data.get("options", []):
                lines.append(f"  - [{opt.get('id')}] {opt.get('label')}: {opt.get('description')}")
        return "\n".join(lines) if lines else "无选项上下文"

    def _format_requirement(self, requirement: dict) -> str:
        lines = []
        for key, value in requirement.items():
            if isinstance(value, list):
                lines.append(f"- {key}:")
                lines.extend([f"  - {item}" for item in value])
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines) if lines else "无"

    def _format_parsed_selections(self, parsed: dict) -> str:
        lines = ["成功解析的选择："]
        for item in parsed.get("successful", []):
            lines.append(f"- 问题 {item.get('question_id')}: {item.get('selected_option', {}).get('label')}")
            lines.append(f"  影响：{item.get('requirement_impact')}")
        if parsed.get("failed"):
            lines.append("解析失败：" + ", ".join(parsed.get("failed")))
        return "\n".join(lines)

    def _assess_context_completeness(self, context: dict) -> str:
        required_fields = ["current_requirement", "conversation_history"]
        present = [f for f in required_fields if f in context]
        return f"{len(present)}/{len(required_fields)}"
