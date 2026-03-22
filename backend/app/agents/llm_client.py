import os
from typing import Optional, AsyncIterator

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "apikey-69b8f5c1e4b0c281b94a4c49")
        self.model = os.getenv("LLM_MODEL", "Qwen3.5-35B-A3B")
        self.base_url = os.getenv("LLM_BASE_URL", "https://modelapi-test.haier.net/model/v1")

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        if not self.api_key:
            return self._generate_mock_response(prompt)
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=2048,
                stream=False,
            )
            msg = response.choices[0].message
            return msg.content or msg.reasoning or ""
        except Exception as e:
            print(f"LLM API Error: {e}")
            return self._generate_mock_response(prompt)

    async def generate_stream(self, prompt: str, temperature: float = 0.7) -> AsyncIterator[str]:
        if not self.api_key:
            yield self._generate_mock_response(prompt)
            return
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            response = await client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=2048,
                stream=True,
            )
            async for chunk in response:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    content = delta.content or delta.reasoning or ""
                    if content:
                        yield content
        except Exception as e:
            print(f"LLM Stream API Error: {e}")
            yield self._generate_mock_response(prompt)

    def _generate_mock_response(self, prompt: str) -> str:
        if "core_requirement" in prompt or "ambiguous_points" in prompt:
            return """{
    "core_requirement": "建立一个需求收敛智能体系统，帮助用户明确和规范化软件需求",
    "identified_points": [
        {"type": "功能", "content": "需求理解和重述", "priority": "高", "keywords": ["理解", "重述"]},
        {"type": "功能", "content": "问题设计和生成", "priority": "高", "keywords": ["问题", "设计"]},
        {"type": "功能", "content": "选项生成和管理", "priority": "中", "keywords": ["选项", "生成"]},
        {"type": "功能", "content": "文档自动生成", "priority": "高", "keywords": ["文档", "生成"]}
    ],
    "ambiguous_points": [
        {"point": "目标用户群体不明确", "question": "您的目标用户是哪些人群？是专业开发人员还是普通用户？", "importance": "高"},
        {"point": "技术栈偏好未说明", "question": "您是否有特定的技术栈偏好？", "importance": "中"},
        {"point": "系统规模不清晰", "question": "预计系统的用户规模和并发量是多少？", "importance": "中"}
    ],
    "confidence": 0.75,
    "missing_info": ["目标用户", "技术栈", "系统规模"]
}"""
        elif "project_overview" in prompt or "core_functions" in prompt:
            return """{
    "project_overview": "建立一个需求收敛智能体系统，通过多轮对话方式帮助用户明确软件需求，生成结构化的需求规格说明书。系统采用多智能体协作架构，各智能体分工明确，实现从需求理解到文档生成的完整流程。",
    "core_functions": [
        "用户需求自动理解和结构化重述",
        "基于模糊点自动生成澄清问题",
        "为每个问题生成多选项供用户选择",
        "处理用户响应并判断需求清晰度",
        "生成符合规范的的需求规格说明书"
    ],
    "target_users": "需要明确项目需求的团队或个人开发者",
    "expected_outcomes": [
        "结构化的需求规格说明书",
        "清晰的功能和非功能需求列表",
        "明确的验收标准和约束条件"
    ],
    "success_criteria": [
        "能够准确理解用户需求",
        "能够识别并澄清模糊点",
        "生成符合规范要求的文档"
    ],
    "known_constraints": [
        "需要用户配合进行多轮对话",
        "生成质量依赖于用户输入的清晰度"
    ]
}"""
        elif "questions" in prompt.lower():
            return """[
    {
        "id": "q1",
        "question": "您的目标用户是哪些人群？",
        "type": "clarification",
        "purpose": "明确系统面向的使用者，以便设计合适的交互方式",
        "priority": "high",
        "options": [
            {"id": "q1_o1", "label": "专业开发人员", "description": "具有技术背景，熟悉软件开发流程"},
            {"id": "q1_o2", "label": "产品经理", "description": "负责产品规划，有一定技术理解但不是开发人员"},
            {"id": "q1_o3", "label": "普通用户/客户", "description": "非技术人员，需要更简单的表达方式"},
            {"id": "q1_o4", "label": "混合用户", "description": "多种用户类型的组合"}
        ]
    },
    {
        "id": "q2",
        "question": "您对技术栈有什么偏好或限制吗？",
        "type": "constraint",
        "purpose": "了解技术选型的约束条件",
        "priority": "medium",
        "options": [
            {"id": "q2_o1", "label": "无限制", "description": "可以自由选择最合适的技术栈"},
            {"id": "q2_o2", "label": "前端限制", "description": "指定前端技术，如React/Vue/Angular等"},
            {"id": "q2_o3", "label": "后端限制", "description": "指定后端技术，如Python/Java/Go等"},
            {"id": "q2_o4", "label": "全栈限制", "description": "指定完整技术栈"}
        ]
    },
    {
        "id": "q3",
        "question": "预计系统的用户规模和并发量是多少？",
        "type": "exploration",
        "purpose": "评估系统性能需求和架构设计",
        "priority": "medium",
        "options": [
            {"id": "q3_o1", "label": "小型（<100用户）", "description": "个人或小团队使用，并发量低"},
            {"id": "q3_o2", "label": "中型（100-1000用户）", "description": "中小团队使用，需要考虑一定并发"},
            {"id": "q3_o3", "label": "大型（>1000用户）", "description": "企业级使用，需要高并发设计"}
        ]
    }
]"""
        elif "options" in prompt.lower() or "recommended" in prompt.lower():
            return """[
    {
        "question_id": "q1",
        "options": [
            {
                "id": "q1_o1",
                "label": "专业开发人员",
                "description": "具有技术背景，熟悉软件开发流程",
                "pros": ["可以使用技术术语", "理解能力强", "可以处理复杂逻辑"],
                "cons": ["可能过于自信", "可能忽略非技术细节"],
                "is_recommended": true,
                "reason": "作为需求收敛系统，专业开发人员能更准确地表达和理解技术需求，这是最匹配的用户群体"
            }
        ]
    }
]"""
        elif "response" in prompt.lower() or "selection" in prompt.lower():
            return """{
    "selections": {
        "q1": {"selected_id": "q1_o1", "selected_label": "专业开发人员"},
        "q2": {"selected_id": "q2_o1", "selected_label": "无限制"},
        "q3": {"selected_id": "q3_o1", "selected_label": "小型（<100用户）"}
    },
    "analysis": {
        "clarity_score": 0.75,
        "remaining_ambiguous": ["交互方式细节", "具体功能优先级"],
        "confidence": "medium"
    },
    "next_action": "continue",
    "reason": "用户已回答大部分关键问题，但仍有少量模糊点需要澄清"
}"""
        elif "document" in prompt.lower() or "generation" in prompt.lower():
            return """{
    "outline": {
        "1. 项目概述": {
            "1.1 项目背景": "需求收敛智能体系统旨在通过AI技术帮助用户明确和规范化软件需求。",
            "1.2 项目目标": "建立一个高效的需求获取和文档生成系统。",
            "1.3 术语定义": "需求收敛：指通过多轮对话逐步明确和确认需求的过程。"
        },
        "2. 功能需求": {
            "2.1 核心功能": "1. 需求理解与重述 2. 问题生成 3. 选项生成 4. 响应处理 5. 文档生成",
            "2.2 用户交互功能": "提供友好的对话界面，支持多轮交互。",
            "2.3 数据管理功能": "管理会话历史和生成的需求文档。",
            "2.4 业务规则": "遵循需求工程最佳实践。"
        },
        "3. 非功能需求": {
            "3.1 性能需求": "响应时间<3秒，支持并发用户。",
            "3.2 安全性需求": "用户认证和数据加密。",
            "3.3 可靠性需求": "系统可用性>99%。",
            "3.4 可维护性需求": "模块化设计，便于维护。",
            "3.5 易用性需求": "界面友好，易于上手。"
        },
        "4. 约束条件": {
            "4.1 技术约束": "Python + FastAPI + React技术栈。",
            "4.2 资源约束": "开发周期3个月。",
            "4.3 法规约束": "遵守数据保护法规。",
            "4.4 兼容性约束": "支持主流浏览器。"
        },
        "5. 验收标准": {
            "5.1 功能验收标准": "所有核心功能可正常使用。",
            "5.2 质量验收标准": "性能和安全指标达标。",
            "5.3 交付物要求": "源代码、文档、部署手册。"
        }
    },
    "is_complete": true
}"""
        return '{"result": "处理完成"}'


_client: Optional[LLMClient] = None

def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
