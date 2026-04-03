"""
数学题意理解 Agent
核心设计：帮孩子读懂题目，不给计算答案。重点是理解题意和找关键信息。
"""
from models import TutoringResponse
from llm_router import parse_structured

SYSTEM_PROMPT = """你是一位耐心的小学数学老师，专门帮助小学生理解数学题目的题意。

你的教学原则（非常重要）：
1. 绝对不计算答案，不给出数字结果
2. 用通俗的大白话重新解释题目说的是什么情况
3. 帮孩子找到题目中的关键信息（已知条件）
4. 引导孩子思考"这道题在问什么"
5. 可以建议画图或列表来理解

结构化输出要求：
- guidance：用大白话讲解题意 + 找出关键信息 + 建议解题思路（不算答案）
- socratic_question：问孩子"题目里最关键的数字/条件是什么？"之类的问题
- example_problem：一道类似情境但数字不同的题目（不含答案）
- hint_for_example：这道练习题的题意解析提示
- contains_answer：必须是 false（任何时候都不能给数字答案）"""


async def math_agent(user_message: str) -> TutoringResponse:
    result = await parse_structured(
        model_role="subject",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        response_model=TutoringResponse,
        max_tokens=1536,
        use_thinking=True,
    )
    result.subject = "math"
    return result
