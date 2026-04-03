"""
错题分析 Agent
核心设计：分析错误原因，理解错在哪里，给出类似例题避免重复犯错。
"""
from models import TutoringResponse, EvaluationResponse
from llm_router import parse_structured

SYSTEM_PROMPT = """你是一位善于分析的小学辅导老师，专门帮助小学生分析错题、找到问题根源。

你的分析框架：
1. 判断错误类型（题意理解错误？计算粗心？知识点不熟？）
2. 指出哪里想错了，但不直接给正确答案
3. 给出避免类似错误的学习建议
4. 提供一道类似的题目让孩子重新尝试

结构化输出要求：
- guidance：分析错误原因 + 指出错误思路（不给正确答案）+ 学习建议
- socratic_question：问孩子"你觉得你是在哪一步想错了？"引导反思
- example_problem：一道类似的题目（数字或情境稍作变化）
- hint_for_example：做这道练习题时要特别注意的地方
- contains_answer：必须是 false"""

EVALUATE_SYSTEM_PROMPT = """你是一位鼓励式教学的小学老师。
孩子刚刚回答了你的问题，请给予正向评价。
即使答案不完全正确，也要找到孩子回答中好的部分，给予鼓励，并温和纠正。
绝对不能打击孩子的积极性。"""


async def mistakes_agent(user_message: str) -> TutoringResponse:
    result = await parse_structured(
        model_role="subject",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        response_model=TutoringResponse,
        max_tokens=1536,
        use_thinking=True,
    )
    result.subject = "mistake"
    return result


async def evaluate_student_answer(
    original_problem: str,
    student_answer: str,
    subject: str,
) -> EvaluationResponse:
    return await parse_structured(
        model_role="evaluate",
        system_prompt=EVALUATE_SYSTEM_PROMPT,
        user_message=f"原题：{original_problem}\n孩子的回答：{student_answer}\n学科：{subject}",
        response_model=EvaluationResponse,
        max_tokens=512,
    )
