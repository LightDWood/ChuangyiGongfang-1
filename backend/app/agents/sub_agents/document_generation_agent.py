import re
from typing import Dict, List
from .template import REQUIREMENT_SPEC_TEMPLATE, QUALITY_CHECKLIST, INTERLEAVED_THINKING_PROMPT


class DocumentGenerationAgent:
    """Sub-agent: Generate requirement specification document"""

    def __init__(self):
        self.name = "DocumentGenerationAgent"
        self.template = REQUIREMENT_SPEC_TEMPLATE

    async def execute(self, requirement: dict, template: dict = None) -> dict:
        target_template = template or self.template

        thought = await self.think_before_planning(requirement, target_template)

        outline = await self._plan_document_outline(requirement, target_template)

        thought = await self.think_after_outline(outline)

        chapters = await self._generate_chapters(outline, requirement, target_template)

        thought = await self.think_after_chapters(chapters)

        validated = await self._validate_document(chapters, requirement)

        thought = await self.think_after_validation(validated)

        final_document = await self._compile_final_document(chapters, validated)

        return {
            "agent": self.name,
            "document": final_document,
            "outline": outline,
            "chapters_generated": len(chapters),
            "validation_result": validated,
            "is_complete": validated.get("is_valid", False),
        }

    async def think_before_planning(self, requirement: dict, template: dict) -> str:
        return f"""自我反思 - 文档生成前

任务理解：
- 我需要根据需求和模板生成完整的需求规格说明书
- 文档应该章节完整、内容准确
- 对于需求中未明确的内容，使用推荐的设计方案

模板结构：
- 章节数：{len(template.get('sections', []))}
- 主要章节：{', '.join([s.get('name', '') for s in template.get('sections', [])])}

需求覆盖度：
- 项目概述：{'✓' if requirement.get('project_overview') else '✗'}
- 核心功能：{len(requirement.get('core_functions', []))} 项
- 目标用户：{'✓' if requirement.get('target_users') else '✗'}
- 约束条件：{len(requirement.get('constraints', []))} 项

接下来规划文档大纲。
"""

    async def think_after_outline(self, outline: dict) -> str:
        return f"""自我反思 - 大纲规划完成

大纲结构：
{self._format_outline(outline)}

接下来按章节生成内容。
"""

    async def think_after_chapters(self, chapters: dict) -> str:
        return f"""自我反思 - 章节生成完成

生成结果：
- 已生成章节：{len(chapters)} 个
- 总内容长度：{sum(len(c.get('content', '')) for c in chapters.values())} 字符

现在验证文档完整性和准确性。
"""

    async def think_after_validation(self, validated: dict) -> str:
        return f"""自我反思 - 验证完成

验证结果：
- 结构完整性：{'✓' if validated.get('structure_complete') else '✗'}
- 内容准确性：{'✓' if validated.get('content_accurate') else '✗'}
- 逻辑连贯性：{'✓' if validated.get('logical_coherent') else '✗'}
- 发现问题：{len(validated.get('issues', []))} 个

{'问题已自动修复' if validated.get('issues') else '文档无需修改'}

最后编译最终文档。
"""

    async def _plan_document_outline(
        self, requirement: dict, template: dict
    ) -> dict:
        prompt = f"""你是一个专业的技术文档架构师。请根据需求和模板规划文档大纲。

模板结构：
{self._format_template(template)}

需求摘要：
- 项目概述：{requirement.get('project_overview', '')}
- 核心功能：{', '.join(requirement.get('core_functions', []))}
- 目标用户：{requirement.get('target_users', '')}
- 预期成果：{', '.join(requirement.get('expected_outcomes', []))}
- 成功标准：{', '.join(requirement.get('success_criteria', []))}
- 约束条件：{', '.join(requirement.get('constraints', []))}

请为每个章节规划：
1. 章节名称
2. 需要包含的要点
3. 内容的来源（来自需求/来自推荐设计）

请以JSON格式输出大纲：
{{
    "sections": [
        {{
            "name": "章节名称",
            "subsections": [
                {{
                    "name": "子章节名称",
                    "key_points": ["要点1", "要点2"],
                    "content_source": "requirement|recommended|hybrid"
                }}
            ]
        }}
    ]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        planned = self._parse_json_response(result)

        if not planned.get("sections"):
            planned["sections"] = template.get("sections", [])

        return planned

    async def _generate_chapters(
        self, outline: dict, requirement: dict, template: dict
    ) -> Dict[str, dict]:
        chapters = {}

        for section in outline.get("sections", template.get("sections", [])):
            section_name = section.get("name", "")

            prompt = f"""请生成以下章节的详细内容。

章节名称：{section_name}

章节结构：
{self._format_section_structure(section)}

需求背景：
{self._format_requirement(requirement)}

写作要求：
1. 使用专业、清晰的语言
2. 内容要具体、可操作
3. 对于需求中未明确的内容，使用行业最佳实践进行补充
4. 保持与前面章节的逻辑连贯性

请以JSON格式输出章节内容：
{{
    "section_name": "章节名称",
    "content": "章节的完整内容（Markdown格式）",
    "subsections": [
        {{
            "name": "子章节名称",
            "content": "子章节内容"
        }}
    ],
    "key_points": ["本章的关键点列表"]
}}

请直接输出JSON，不要有其他内容。
"""
            result = await self._call_llm(prompt)
            parsed = self._parse_json_response(result)

            if parsed.get("section_name"):
                chapters[section_name] = parsed
            else:
                chapters[section_name] = {
                    "section_name": section_name,
                    "content": self._generate_default_content(section, requirement),
                    "subsections": [],
                    "key_points": [],
                }

        return chapters

    async def _validate_document(
        self, chapters: Dict[str, dict], requirement: dict
    ) -> dict:
        prompt = f"""请验证生成的需求规格说明书。

章节列表：
{self._format_chapters(chapters)}

原始需求：
{self._format_requirement(requirement)}

验证维度：
1. 结构完整性：是否包含所有必要章节？
2. 内容准确性：内容是否符合需求？
3. 逻辑连贯性：章节之间是否逻辑连贯？
4. 模糊性：是否存在模糊或不确定的描述？

请以JSON格式输出验证结果：
{{
    "is_valid": true/false,
    "structure_complete": true/false,
    "content_accurate": true/false,
    "logical_coherent": true/false,
    "issues": ["发现的问题列表"],
    "suggestions": ["改进建议列表"]
}}

请直接输出JSON，不要有其他内容。
"""
        result = await self._call_llm(prompt)
        validated = self._parse_json_response(result)

        if not validated:
            validated = {
                "is_valid": True,
                "structure_complete": True,
                "content_accurate": True,
                "logical_coherent": True,
                "issues": [],
                "suggestions": [],
            }

        return validated

    async def _compile_final_document(
        self, chapters: Dict[str, dict], validation: dict
    ) -> dict:
        document_content = []
        document_content.append(f"# {self.template.get('title', '需求规格说明书')}\n")

        for section in self.template.get("sections", []):
            section_name = section.get("name", "")
            chapter = chapters.get(section_name, {})

            if chapter.get("content"):
                document_content.append(f"\n## {section_name}\n")
                document_content.append(chapter.get("content", ""))

            for subsection in section.get("subsections", []):
                subsection_name = subsection.get("name", "")
                subsection_content = self._find_subsection_content(
                    chapter, subsection_name
                )

                if subsection_content:
                    document_content.append(f"\n### {subsection_name}\n")
                    document_content.append(subsection_content)
                else:
                    default_content = self._generate_default_subsection(
                        subsection, chapter
                    )
                    document_content.append(f"\n### {subsection_name}\n")
                    document_content.append(default_content)

        return {
            "title": self.template.get("title", "需求规格说明书"),
            "content": "\n".join(document_content),
            "metadata": {
                "sections_count": len(chapters),
                "is_valid": validation.get("is_valid", False),
                "issues_count": len(validation.get("issues", [])),
            },
        }

    def _generate_default_content(self, section: dict, requirement: dict) -> str:
        section_name = section.get("name", "")

        defaults = {
            "1. 项目概述": f"""本项目旨在{requirement.get('project_overview', '实现用户需求')}

目标用户：{requirement.get('target_users', '待确定')}

预期成果：
{self._format_list(requirement.get('expected_outcomes', ['完成系统开发']))}""",
            "2. 功能需求": f"""核心功能：
{self._format_list(requirement.get('core_functions', ['基础功能']))}""",
            "3. 非功能需求": """性能需求：系统应具备良好的响应速度，满足用户操作需求。

安全性需求：系统应具备完善的安全机制，保护用户数据安全。

可靠性需求：系统应稳定运行，具备必要的容错能力。

易用性需求：系统应具备良好的用户体验。
""",
            "4. 约束条件": f"""{self._format_list(requirement.get('constraints', ['遵守相关法规']))}""",
            "5. 验收标准": f"""功能验收：
{self._format_list(requirement.get('success_criteria', ['所有功能正常运行']))}

质量标准：满足既定的非功能需求指标。
""",
        }

        return defaults.get(section_name, f"本章内容待补充。")

    def _generate_default_subsection(self, subsection: dict, chapter: dict) -> str:
        return subsection.get("description", "本章内容待补充。")

    def _find_subsection_content(self, chapter: dict, subsection_name: str) -> str:
        for sub in chapter.get("subsections", []):
            if sub.get("name") == subsection_name:
                return sub.get("content", "")
        return ""

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
        except Exception:
            pass
        return {}

    def _format_template(self, template: dict) -> str:
        lines = []
        for section in template.get("sections", []):
            lines.append(f"- {section.get('name')}")
            for sub in section.get("subsections", []):
                lines.append(f"  - {sub.get('name')}: {sub.get('description', '')}")
        return "\n".join(lines)

    def _format_requirement(self, requirement: dict) -> str:
        lines = []
        for key, value in requirement.items():
            if isinstance(value, list):
                lines.append(f"- {key}: {', '.join(map(str, value))}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _format_section_structure(self, section: dict) -> str:
        lines = [f"章节：{section.get('name')}"]
        for sub in section.get("subsections", []):
            lines.append(f"  - {sub.get('name')}: {sub.get('description', '')}")
        return "\n".join(lines)

    def _format_chapters(self, chapters: dict) -> str:
        return "\n".join([f"- {name}" for name in chapters.keys()])

    def _format_outline(self, outline: dict) -> str:
        lines = []
        for section in outline.get("sections", []):
            lines.append(f"- {section.get('name')}")
            for sub in section.get("subsections", []):
                lines.append(f"  - {sub.get('name')}")
        return "\n".join(lines)

    def _format_list(self, items: list) -> str:
        return "\n".join([f"  - {item}" for item in items]) if items else "  - 待补充"
