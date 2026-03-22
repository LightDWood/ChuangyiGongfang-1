REQUIREMENT_SPEC_TEMPLATE = {
    "title": "需求规格说明书",
    "sections": [
        {
            "name": "1. 项目概述",
            "subsections": [
                {"name": "1.1 项目背景", "description": "描述项目产生的背景和动机"},
                {"name": "1.2 项目目标", "description": "明确项目要达到的核心目标"},
                {"name": "1.3 术语定义", "description": "定义文档中使用的关键术语"},
            ]
        },
        {
            "name": "2. 功能需求",
            "subsections": [
                {"name": "2.1 核心功能", "description": "系统必须实现的核心功能模块"},
                {"name": "2.2 用户交互功能", "description": "用户与系统交互相关的功能"},
                {"name": "2.3 数据管理功能", "description": "数据的增删改查等管理功能"},
                {"name": "2.4 业务规则", "description": "系统需要遵守的业务规则"},
            ]
        },
        {
            "name": "3. 非功能需求",
            "subsections": [
                {"name": "3.1 性能需求", "description": "系统的性能指标要求"},
                {"name": "3.2 安全性需求", "description": "系统的安全性和权限控制要求"},
                {"name": "3.3 可靠性需求", "description": "系统的可用性和容错要求"},
                {"name": "3.4 可维护性需求", "description": "系统的可扩展性和可维护性要求"},
                {"name": "3.5 易用性需求", "description": "用户体验相关的要求"},
            ]
        },
        {
            "name": "4. 约束条件",
            "subsections": [
                {"name": "4.1 技术约束", "description": "技术选型和架构限制"},
                {"name": "4.2 资源约束", "description": "时间、人力、资金等资源限制"},
                {"name": "4.3 法规约束", "description": "需要遵守的法律法规要求"},
                {"name": "4.4 兼容性约束", "description": "与现有系统的兼容性要求"},
            ]
        },
        {
            "name": "5. 验收标准",
            "subsections": [
                {"name": "5.1 功能验收标准", "description": "功能是否满足的判定标准"},
                {"name": "5.2 质量验收标准", "description": "非功能需求的验收判定标准"},
                {"name": "5.3 交付物要求", "description": "需要交付的文档和制品"},
            ]
        },
    ]
}

QUESTION_DESIGN_GUIDELINES = {
    "question_types": {
        "clarification": "澄清型问题 - 明确模糊或不确定的需求点",
        "confirmation": "确认型问题 - 确认已理解的需求是否正确",
        "exploration": "探索型问题 - 深入了解用户的真实需求和优先级",
        "constraint": "约束型问题 - 了解项目约束和限制条件",
        "preference": "偏好型问题 - 了解用户对技术方案或设计风格的偏好",
    },
    "design_principles": [
        "每个问题应聚焦于一个具体的点",
        "问题应使用简单易懂的语言",
        "问题应按照逻辑顺序排列",
        "关键问题应放在前面",
        "应提供选项帮助用户回答",
    ],
    "max_questions_per_round": 5,
}

OPTION_GENERATION_GUIDELINES = {
    "min_options": 2,
    "max_options": 4,
    "recommended_option_index": 0,
    "option_structure": {
        "label": "选项标签",
        "description": "选项详细描述",
        "pros": "选择此选项的优势",
        "cons": "选择此选项的潜在问题",
        "is_recommended": "是否为推荐选项",
        "reason": "推荐理由",
    }
}

QUALITY_CHECKLIST = {
    "requirement_understanding": [
        "是否准确理解了用户的核心需求？",
        "是否识别出了需求中的模糊点？",
        "是否遗漏了重要的上下文信息？",
        "重述的需求是否清晰易懂？",
    ],
    "question_design": [
        "问题是否覆盖了所有模糊点？",
        "问题是否具有逻辑顺序？",
        "问题是否简洁明了？",
        "问题是否便于用户回答？",
    ],
    "option_generation": [
        "选项是否全面覆盖了可能的答案？",
        "推荐选项是否有充分的理由支持？",
        "选项描述是否客观中立？",
        "选项之间是否有足够的区分度？",
    ],
    "response_processing": [
        "是否正确理解了用户的每个选择？",
        "是否准确判断了需求的清晰程度？",
        "是否正确决定了下一步行动？",
    ],
    "document_generation": [
        "文档结构是否符合模板要求？",
        "内容是否完整覆盖了所有需求？",
        "描述是否准确、无歧义？",
        "章节之间是否有逻辑连贯性？",
    ]
}

INTERLEAVED_THINKING_PROMPT = """
在执行每一步操作时，先进行自我反思（think），然后再执行操作。

自我反思应包括：
1. 我当前要完成什么任务？
2. 我的上一步输出是否合理？
3. 我接下来应该怎么做？
4. 我的输出是否能帮助下一个代理？

将自我反思插入到关键步骤之间，确保每个主要操作前后都有反思。
"""
