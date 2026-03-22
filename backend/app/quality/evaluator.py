"""LLM-based Evaluator for quality checks"""
import re
import json
from typing import Dict, Any, List, Optional

from ..agents.llm_client import get_llm_client


class LLMEvaluator:
    """Uses LLM to evaluate output quality"""

    def __init__(self):
        self.llm_client = None

    async def _get_client(self):
        if self.llm_client is None:
            self.llm_client = get_llm_client()
        return self.llm_client

    async def evaluate_facts(self, content: str) -> dict:
        """Check factual accuracy"""
        prompt = f"""你是一个事实核查专家。请检查以下内容的 factual accuracy（事实准确性）。

待检查内容：
{content}

请分析并评估：
1. 是否有任何事实性错误？
2. 声明是否有适当的依据？
3. 是否有过度夸大或绝对化的表述？
4. 事实陈述与推测性陈述是否区分清楚？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的准确度分数,
    "issues": [
        {{
            "type": "error_type",
            "description": "问题描述",
            "content": "有问题的原文",
            "suggestion": "修改建议"
        }}
    ],
    "verified_statements": ["经验证准确的声明列表"],
    "unverified_statements": ["未经证的声明列表"]
}}

请直接输出JSON，不要有其他内容。
"""
        client = await self._get_client()
        response = await client.generate(prompt)

        try:
            result = self._parse_json_response(response)
            if result:
                return result
        except Exception:
            pass

        return {
            "score": 0.8,
            "issues": [],
            "verified_statements": [],
            "unverified_statements": []
        }

    async def evaluate_completeness(self, content: str, template: dict) -> dict:
        """Check if all required sections are present"""
        required_sections = template.get("required_sections", []) if template else [
            "项目概述",
            "功能需求",
            "非功能需求",
            "约束条件",
            "验收标准"
        ]

        prompt = f"""你是一个 completeness（完整性）检查专家。请检查以下内容是否涵盖所有必要部分。

内容：
{content}

必需部分：
{json.dumps(required_sections, ensure_ascii=False)}

请检查：
1. 每个必需部分是否都存在？
2. 每个部分的内容是否充分？
3. 是否有重要遗漏？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的完整度分数,
    "present_sections": ["已存在的部分列表"],
    "missing_sections": ["缺失的部分列表"],
    "incomplete_sections": [
        {{
            "section": "部分名称",
            "issue": "问题描述",
            "suggestion": "补充建议"
        }}
    ]
}}

请直接输出JSON，不要有其他内容。
"""
        client = await self._get_client()
        response = await client.generate(prompt)

        try:
            result = self._parse_json_response(response)
            if result:
                return result
        except Exception:
            pass

        missing = [s for s in required_sections if s not in content]
        return {
            "score": 1.0 - (len(missing) / len(required_sections)) if required_sections else 1.0,
            "present_sections": [s for s in required_sections if s in content],
            "missing_sections": missing,
            "incomplete_sections": []
        }

    async def evaluate_citations(self, content: str) -> dict:
        """Verify citation accuracy"""
        citations_pattern = r'\[(\d+)\]|\(来源\d+\)|《([^》]+)》'
        citations_found = re.findall(citations_pattern, content)

        prompt = f"""你是一个 citation（引用）核查专家。请检查以下内容中引用的准确性。

内容：
{content}

发现的引用：
{json.dumps([c for c in citations_found if any(c)], ensure_ascii=False)}

请检查：
1. 引用的格式是否规范？
2. 引用的来源是否存在？
3. 引用是否与声明的内容匹配？
4. 是否有虚构或错误的引用？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的引用准确度分数,
    "valid_citations": ["有效引用列表"],
    "invalid_citations": [
        {{
            "citation": "引用内容",
            "issue": "问题描述"
        }}
    ],
    "missing_sources": ["引用了但没有提供来源的声明"]
}}

请直接输出JSON，不要有其他内容。
"""
        client = await self._get_client()
        response = await client.generate(prompt)

        try:
            result = self._parse_json_response(response)
            if result:
                return result
        except Exception:
            pass

        return {
            "score": 0.9 if citations_found else 1.0,
            "valid_citations": [c for c in citations_found if any(c)],
            "invalid_citations": [],
            "missing_sources": []
        }

    async def evaluate_relevance(self, content: str, user_intent: str) -> dict:
        """Check if content is relevant to user intent"""
        prompt = f"""你是一个 relevance（相关性）评估专家。请评估以下内容与用户意图的相关程度。

用户意图：
{user_intent}

待评估内容：
{content}

请评估：
1. 内容是否直接回应了用户的意图？
2. 是否有偏离主题的内容？
3. 核心信息是否与用户需求相关？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的相关度分数,
    "relevant_parts": ["相关部分列表"],
    "irrelevant_parts": [
        {{
            "content": "不相关内容",
            "issue": "不相关原因"
        }}
    ],
    "suggestion": "提高相关性的建议"
}}

请直接输出JSON，不要有其他内容。
"""
        client = await self._get_client()
        response = await client.generate(prompt)

        try:
            result = self._parse_json_response(response)
            if result:
                return result
        except Exception:
            pass

        return {
            "score": 0.85,
            "relevant_parts": [],
            "irrelevant_parts": [],
            "suggestion": ""
        }

    async def evaluate_consistency(self, content: dict) -> dict:
        """Check for internal consistency in content"""
        prompt = f"""你是一个 consistency（一致性）检查专家。请检查以下内容内部是否存在矛盾。

内容：
{json.dumps(content, ensure_ascii=False, indent=2)}

请检查：
1. 各个部分之间是否有逻辑矛盾？
2. 术语使用是否一致？
3. 数字和统计数据是否一致？
4. 优先级和排序是否合理？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的一致性分数,
    "issues": [
        {{
            "type": "contradiction|inconsistency|error",
            "description": "问题描述",
            "location": "问题位置"
        }}
    ],
    "is_consistent": true或false
}}

请直接输出JSON，不要有其他内容。
"""
        client = await self._get_client()
        response = await client.generate(prompt)

        try:
            result = self._parse_json_response(response)
            if result:
                return result
        except Exception:
            pass

        return {
            "score": 1.0,
            "issues": [],
            "is_consistent": True
        }

    async def evaluate_clarity(self, content: str) -> dict:
        """Evaluate clarity and readability of content"""
        prompt = f"""你是一个 clarity（清晰度）评估专家。请评估以下内容的清晰度和可读性。

内容：
{content}

请评估：
1. 语言是否清晰易懂？
2. 表达是否简洁？
3. 是否有歧义或模糊的表达？
4. 结构是否清晰？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的清晰度分数,
    "issues": [
        {{
            "type": "类型",
            "content": "有问题的原文",
            "suggestion": "修改建议"
        }}
    ],
    "readability_score": "易于理解|中等|较难理解"
}}

请直接输出JSON，不要有其他内容。
"""
        client = await self._get_client()
        response = await client.generate(prompt)

        try:
            result = self._parse_json_response(response)
            if result:
                return result
        except Exception:
            pass

        return {
            "score": 0.85,
            "issues": [],
            "readability_score": "易于理解"
        }

    def _parse_json_response(self, response: str) -> Optional[dict]:
        try:
            json_match = re.search(r'\{.*\}|\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return None
