"""Specific quality check implementations"""
import re
from typing import Dict, Any, List, Optional

from ..agents.llm_client import get_llm_client


class QualityChecks:
    """Specific quality check implementations"""

    def __init__(self):
        self.llm_client = None

    async def _get_client(self):
        if self.llm_client is None:
            self.llm_client = get_llm_client()
        return self.llm_client

    async def check_requirement_clarity(self, requirement: dict) -> dict:
        """Check if requirement is clearly stated"""
        content = requirement.get("content", "")
        issues = []
        score = 1.0

        if not content or len(content.strip()) == 0:
            return {
                "score": 0.0,
                "is_clear": False,
                "issues": ["Requirement content is empty"]
            }

        if len(content) < 10:
            issues.append({"type": "too_short", "description": "需求描述过短"})
            score -= 0.3

        if len(content) > 500:
            issues.append({"type": "too_long", "description": "需求描述过长，可能包含过多细节"})
            score -= 0.2

        vague_keywords = ["等等", "之类", "什么的", "大概", "可能"]
        for keyword in vague_keywords:
            if keyword in content:
                issues.append({"type": "vague", "keyword": keyword, "description": f"包含模糊词汇: {keyword}"})
                score -= 0.15

        absolute_keywords = ["所有", "每个", "全部", "必须", "一定"]
        has_absolutes = any(kw in content for kw in absolute_keywords)
        if has_absolutes:
            issues.append({"type": "absolute", "description": "包含绝对性表述，可能过于严格"})
            score -= 0.1

        prompt = f"""请评估以下需求描述的清晰度：

需求内容：
{content}

请检查：
1. 是否有明确的执行主体？
2. 是否有明确的动作和结果？
3. 是否有模糊不清的表述？
4. 是否易于理解？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的清晰度分数,
    "is_clear": true或false,
    "issues": [
        {{
            "type": "问题类型",
            "description": "问题描述"
        }}
    ],
    "suggestions": ["改进建议列表"]
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
            "score": max(0.0, score),
            "is_clear": score >= 0.7,
            "issues": issues,
            "suggestions": []
        }

    async def check_option_quality(self, options: list) -> dict:
        """Check quality of generated options"""
        if not options:
            return {
                "score": 0.0,
                "is_valid": False,
                "issues": [{"type": "empty", "description": "选项列表为空"}]
            }

        issues = []
        score = 1.0

        if len(options) < 2:
            issues.append({"type": "too_few", "description": "选项数量不足，建议至少2个选项"})
            score -= 0.3

        if len(options) > 6:
            issues.append({"type": "too_many", "description": "选项数量过多，可能让用户选择困难"})
            score -= 0.1

        option_texts = []
        for opt in options:
            if isinstance(opt, dict):
                text = opt.get("label", "") or opt.get("description", "")
            else:
                text = str(opt)
            option_texts.append(text.lower())

        duplicates = []
        for i, text1 in enumerate(option_texts):
            for j, text2 in enumerate(option_texts):
                if i < j and text1 == text2:
                    duplicates.append(text1)

        if duplicates:
            issues.append({"type": "duplicate", "description": f"发现重复选项: {duplicates}"})

        vague_options = ["无所谓", "都可以", "其他", "以上都不是"]
        for opt in options:
            label = opt.get("label", "") if isinstance(opt, dict) else str(opt)
            if label in vague_options:
                issues.append({"type": "vague_option", "label": label, "description": "包含模糊选项"})
                score -= 0.1
                break

        prompt = f"""请评估以下选项的质量：

选项列表：
{options}

请检查：
1. 选项是否互不重叠？
2. 选项是否覆盖了主要可能性？
3. 选项描述是否清晰？
4. 选项是否平衡（没有明显偏向某个选项）？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的质量分数,
    "is_valid": true或false,
    "issues": [
        {{
            "type": "问题类型",
            "description": "问题描述"
        }}
    ],
    "suggestions": ["改进建议列表"]
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
            "score": max(0.0, score),
            "is_valid": score >= 0.6,
            "issues": issues,
            "suggestions": []
        }

    async def check_document_completeness(self, document: dict, template: dict) -> dict:
        """Check if document covers all template sections"""
        if not document:
            return {
                "score": 0.0,
                "is_complete": False,
                "missing_sections": ["整个文档为空"]
            }

        required_sections = template.get("required_sections", []) if template else [
            "项目概述",
            "功能需求",
            "非功能需求",
            "约束条件",
            "验收标准"
        ]

        if isinstance(document, str):
            doc_content = document
        else:
            doc_content = json.dumps(document, ensure_ascii=False) if isinstance(document, dict) else str(document)

        missing_sections = []
        present_sections = []
        incomplete_sections = []

        for section in required_sections:
            if section in doc_content:
                present_sections.append(section)
                section_pattern = rf"{section}[\s:：\n]"
                match = re.search(section_pattern, doc_content)
                if match:
                    start = match.end()
                    next_section_idx = len(doc_content)
                    for other_section in required_sections:
                        if other_section != section:
                            idx = doc_content.find(other_section, start)
                            if idx != -1 and idx < next_section_idx:
                                next_section_idx = idx
                    section_content = doc_content[start:next_section_idx]
                    if len(section_content.strip()) < 50:
                        incomplete_sections.append({
                            "section": section,
                            "issue": "内容过短",
                            "current_length": len(section_content.strip())
                        })
            else:
                missing_sections.append(section)

        score = len(present_sections) / len(required_sections) if required_sections else 1.0
        if incomplete_sections:
            score -= len(incomplete_sections) * 0.1

        prompt = f"""请检查以下需求规格文档的完整性：

文档内容：
{doc_content[:2000]}

必需部分：
{required_sections}

请检查：
1. 每个必需部分是否存在？
2. 每个部分的内容是否充分？
3. 是否有重要遗漏？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的完整度分数,
    "is_complete": true或false,
    "present_sections": ["已存在的部分列表"],
    "missing_sections": ["缺失的部分列表"],
    "incomplete_sections": [
        {{
            "section": "部分名称",
            "issue": "问题描述"
        }}
    ],
    "suggestions": ["补充建议"]
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
            "score": max(0.0, score),
            "is_complete": score >= 0.8,
            "present_sections": present_sections,
            "missing_sections": missing_sections,
            "incomplete_sections": incomplete_sections,
            "suggestions": []
        }

    async def check_recommendation_validity(self, recommendation: dict) -> dict:
        """Check if recommendations are reasonable"""
        if not recommendation:
            return {
                "score": 0.0,
                "is_valid": False,
                "issues": [{"type": "empty", "description": "推荐内容为空"}]
            }

        issues = []
        warnings = []
        score = 1.0

        recommendation_text = recommendation.get("content", "") or str(recommendation)

        extreme_keywords = ["绝对", "一定", "所有", "每个", "必须"]
        for keyword in extreme_keywords:
            if keyword in recommendation_text:
                issues.append({
                    "type": "extreme_statement",
                    "keyword": keyword,
                    "description": f"包含极端表述: {keyword}"
                })
                score -= 0.2

        unsupported_keywords = ["据说", "听说", "可能", "也许"]
        for keyword in unsupported_keywords:
            if keyword in recommendation_text:
                warnings.append({
                    "type": "unsupported_claim",
                    "keyword": keyword,
                    "description": f"包含未经支持的声明: {keyword}"
                })
                score -= 0.1

        if "没有" in recommendation_text or "不会" in recommendation_text:
            negative_patterns = [
                (r"没有问题", "声称没有问题可能过于乐观"),
                (r"不会失败", "声称不会失败可能过于自信"),
                (r"不可能.*错误", "声称不可能出错可能过于绝对")
            ]
            for pattern, desc in negative_patterns:
                if re.search(pattern, recommendation_text):
                    warnings.append({
                        "type": "overly_positive",
                        "description": desc
                    })
                    score -= 0.1

        prompt = f"""请评估以下推荐内容的合理性：

推荐内容：
{recommendation}

请检查：
1. 推荐是否有合理的依据？
2. 推荐是否考虑了可能的负面影响？
3. 推荐是否过于绝对或偏颇？
4. 是否有更好的替代方案？

请以JSON格式返回评估结果：
{{
    "score": 0.0-1.0之间的合理度分数,
    "is_valid": true或false,
    "issues": [
        {{
            "type": "问题类型",
            "description": "问题描述"
        }}
    ],
    "warnings": [
        {{
            "type": "警告类型",
            "description": "警告描述"
        }}
    ],
    "suggestions": ["改进建议列表"]
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
            "score": max(0.0, score),
            "is_valid": score >= 0.6,
            "issues": issues,
            "warnings": warnings,
            "suggestions": []
        }

    async def check_citation_format(self, content: str) -> dict:
        """Check if citations are properly formatted"""
        citation_patterns = [
            r'\[\d+\]',
            r'\(\d+\)',
            r'《[^》]+》',
            r'"[^"]+"\s*\(\d{4}\)',
        ]

        found_citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, content)
            found_citations.extend(matches)

        issues = []
        if not found_citations:
            issues.append({
                "type": "no_citations",
                "description": "内容中未发现引用"
            })

        duplicate_pattern = r'(\[\d+\])\s*.*?\1'
        duplicates = re.findall(duplicate_pattern, content)
        if duplicates:
            issues.append({
                "type": "duplicate_citations",
                "description": f"发现重复引用: {set(duplicates)}"
            })

        score = 1.0
        if not found_citations:
            score -= 0.3
        if issues:
            score -= len(issues) * 0.1

        return {
            "score": max(0.0, score),
            "citations_found": found_citations,
            "issues": issues
        }

    async def check_terminology_consistency(self, content: str, terminology_map: dict = None) -> dict:
        """Check terminology consistency throughout content"""
        if terminology_map is None:
            terminology_map = {
                "需求": ["需求", "要求", "需求项"],
                "功能": ["功能", "职能", "作用"],
                "用户": ["用户", "使用者", "终端用户"],
                "系统": ["系统", "平台", "应用"]
            }

        issues = []
        total_variations = 0

        for standard_term, variations in terminology_map.items():
            all_occurrences = []
            for var in variations:
                count = content.count(var)
                all_occurrences.append((var, count))
                total_variations += count

            if total_variations > 0:
                usage = dict(all_occurrences)
                if len([c for c in usage.values() if c > 0]) > 1:
                    issues.append({
                        "type": "inconsistent_terminology",
                        "standard_term": standard_term,
                        "usage": usage,
                        "description": f"'{standard_term}'有多种表达方式"
                    })

        score = 1.0 - (len(issues) * 0.15)

        return {
            "score": max(0.0, score),
            "is_consistent": len(issues) == 0,
            "issues": issues
        }

    def _parse_json_response(self, response: str) -> Optional[dict]:
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                import json
                return json.loads(json_match.group())
        except Exception:
            pass
        return None
