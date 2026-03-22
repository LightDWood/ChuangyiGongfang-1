import re
from typing import Dict, List
from .template import OPTION_GENERATION_GUIDELINES, QUALITY_CHECKLIST, INTERLEAVED_THINKING_PROMPT


class OptionGenerationAgent:
    """Sub-agent: Generate options for each question"""

    def __init__(self):
        self.name = "OptionGenerationAgent"
        self.min_options = OPTION_GENERATION_GUIDELINES.get("min_options", 2)
        self.max_options = OPTION_GENERATION_GUIDELINES.get("max_options", 4)

    async def execute(self, questions: list) -> dict:
        thought = await self.think_before_generation(questions)

        options_by_question = {}
        for question in questions:
            options = await self._generate_options_for_question(question)
            options_by_question[question.get("id")] = {
                "question": question,
                "options": options,
            }

        thought = await self.think_after_generation(options_by_question)

        validated = await self._validate_all_options(options_by_question)

        thought = await self.think_after_validation(validated)

        enhanced = await self._enhance_with_recommendations(validated)

        is_valid = await self._validate_output(enhanced)
        if not is_valid:
            enhanced = await self._refine_options(enhanced)

        return {
            "agent": self.name,
            "options_by_question": enhanced,
            "total_options_generated": sum(
                len(data["options"]) for data in enhanced.values()
            ),
            "questions_with_recommended": sum(
                1 for data in enhanced.values()
                if any(opt.get("is_recommended") for opt in data["options"])
            ),
        }

    async def think_before_generation(self, questions: list) -> str:
        return f"""自我反思 - 选项生成前

任务理解：
- 我需要为每个问题生成 2-4 个选项
- 需要包含推荐选项及理由
- 选项应客观中立

问题概览：
- 问题总数：{len(questions)} 个
- 问题类型分布：{self._count_types(questions)}
- 高优先级问题：{len([q for q in questions if q.get('priority') == 'high'])} 个

接下来为每个问题生成选项。
"""

    async def think_after_generation(self, options_by_question: dict) -> str:
        total_options = sum(len(data["options"]) for data in options_by_question.values())
        questions_with_options = len(
            [q for q in options_by_question.values() if len(q["options"]) >= self.min_options]
        )

        return f"""自我反思 - 选项生成完成

生成结果检查：
- 总选项数：{total_options} 个
- 每个问题选项数：{total_options / max(1, len(options_by_question)):.1f} 个
- 符合最低要求的问题数：{questions_with_options}/{len(options_by_question)}

接下来验证每个选项的质量。
"""

    async def think_after_validation(self, validated: dict) -> str:
        return f"""自我反思 - 验证完成

验证结果：
- 所有选项符合要求：{'✓' if validated else '✗'}
- 推荐选项设置：{sum(1 for data in validated.values() if any(o.get('is_recommended') for o in data['options']))} 个问题

现在为推荐选项添加增强说明，帮助用户理解推荐理由。
"""

    async def _generate_options_for_question(self, question: dict) -> List[dict]:
        prompt = f"""你是一个专业的方案设计专家。请为以下问题生成选项列表。

问题：
- ID：{question.get('id')}
- 内容：{question.get('question')}
- 类型：{question.get('type')}
- 目的：{question.get('purpose')}
- 优先级：{question.get('priority')}

{OPTION_GENERATION_GUIDELINES}

选项生成要求：
- 生成 {self.min_options} 到 {self.max_options} 个选项
- 每个选项包含：label（标签）、description（描述）
- 选项之间应有明显区分度
- 指定一个推荐选项并说明理由

请以JSON格式输出：
{{
    "options": [
        {{
            "id": "{question.get('id')}_o[n]",
            "label": "选项标签",
            "description": "选项详细描述",
            "pros": ["优势1", "优势2"],
            "cons": ["潜在问题1"],
            "is_recommended": true/false,
            "reason": "推荐理由（仅当is_recommended为true时）"
        }}
    ]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        parsed = self._parse_json_response(result)
        return parsed.get("options", [])

    async def _validate_all_options(self, options_by_question: dict) -> dict:
        validated = {}

        for q_id, data in options_by_question.items():
            options = data["options"]
            validated_options = []

            for opt in options:
                if self._validate_single_option(opt):
                    validated_options.append(opt)

            if len(validated_options) < self.min_options:
                validated_options = await self._fix_options(
                    data["question"], validated_options
                )

            validated[q_id] = {
                "question": data["question"],
                "options": validated_options,
            }

        return validated

    async def _enhance_with_recommendations(self, options_by_question: dict) -> dict:
        enhanced = {}

        for q_id, data in options_by_question.items():
            options = data["options"]
            has_recommended = any(opt.get("is_recommended") for opt in options)

            if not has_recommended and options:
                options = await self._set_recommended_option(data["question"], options)
                enhanced[q_id] = {"question": data["question"], "options": options}
            else:
                enhanced[q_id] = data

        return enhanced

    async def _validate_output(self, options_by_question: dict) -> bool:
        checklist = QUALITY_CHECKLIST["option_generation"]

        for q_id, data in options_by_question.items():
            options = data["options"]

            if len(options) < self.min_options or len(options) > self.max_options:
                return False

            for opt in options:
                if not self._check_option_structure(opt):
                    return False

        return True

    async def _refine_options(self, options_by_question: dict) -> dict:
        refined = {}

        for q_id, data in options_by_question.items():
            options = data["options"]

            if len(options) < self.min_options:
                prompt = f"""请补充问题选项。当前只有 {len(options)} 个选项，需要至少 {self.min_options} 个。

问题：{data['question'].get('question')}
当前选项：{self._format_options(options)}

请补充选项，使总数达到 {self.min_options} 到 {self.max_options} 个。

请以JSON格式输出完整的选项列表。
"""
                result = await self._call_llm(prompt)
                parsed = self._parse_json_response(result)
                options = parsed.get("options", options)

            refined[q_id] = {"question": data["question"], "options": options}

        return refined

    async def _fix_options(self, question: dict, current_options: list) -> List[dict]:
        prompt = f"""请修复问题选项。

问题：{question.get('question')}
当前选项数：{len(current_options)} 个（少于最低要求 {self.min_options} 个）

请生成足够的选项，确保有 {self.min_options} 到 {self.max_options} 个选项。

请以JSON格式输出完整的选项列表。
"""
        result = await self._call_llm(prompt)
        parsed = self._parse_json_response(result)
        fixed = parsed.get("options", current_options)

        if len(fixed) < self.min_options:
            default_options = self._get_default_options(question)
            fixed = default_options

        return fixed[: self.max_options]

    async def _set_recommended_option(self, question: dict, options: List[dict]) -> List[dict]:
        if not options:
            return options

        prompt = f"""请为以下问题选项设置推荐选项。

问题：{question.get('question')}
选项数量：{len(options)}

请分析各选项，选择最合适的作为推荐选项，并提供推荐理由。

请以JSON格式输出：
{{
    "options": [
        {{...原始选项..., "is_recommended": true/false, "reason": "推荐理由"}}
    ]
}}
"""
        result = await self._call_llm(prompt)
        parsed = self._parse_json_response(result)
        return parsed.get("options", options)

    def _get_default_options(self, question: dict) -> List[dict]:
        q_type = question.get("type", "clarification")

        defaults = {
            "clarification": [
                {"id": f"{question.get('id')}_o1", "label": "需要", "description": "必须有此功能", "is_recommended": True, "reason": "这是核心需求"},
                {"id": f"{question.get('id')}_o2", "label": "不需要", "description": "不需要此功能", "is_recommended": False},
                {"id": f"{question.get('id')}_o3", "label": "可选", "description": "可以根据情况选择", "is_recommended": False},
            ],
            "constraint": [
                {"id": f"{question.get('id')}_o1", "label": "有严格限制", "description": "这是必须遵守的约束", "is_recommended": True, "reason": "遵循约束是项目成功的基础"},
                {"id": f"{question.get('id')}_o2", "label": "有一定弹性", "description": "可以在一定范围内调整", "is_recommended": False},
                {"id": f"{question.get('id')}_o3", "label": "灵活", "description": "可以根据实际情况调整", "is_recommended": False},
            ],
        }

        return defaults.get(q_type, defaults["clarification"])

    def _validate_single_option(self, option: dict) -> bool:
        required_fields = ["id", "label", "description"]
        return all(field in option and option[field] for field in required_fields)

    def _check_option_structure(self, option: dict) -> bool:
        return bool(option.get("id") and option.get("label"))

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

                return {"options": json.loads(array_match.group())}
        except Exception:
            pass
        return {}

    def _format_options(self, options: list) -> str:
        return "\n".join([f"- {opt.get('label')}: {opt.get('description')}" for opt in options])

    def _count_types(self, questions: list) -> Dict[str, int]:
        counts = {}
        for q in questions:
            q_type = q.get("type", "unknown")
            counts[q_type] = counts.get(q_type, 0) + 1
        return counts
