"""
Router Agent — 意图分类
使用 claude-haiku-4-5（快速、低成本）+ Structured Output 精确分类用户意图
"""
from models import RouterDecision
from llm_router import parse_structured

ROUTER_SYSTEM_PROMPT = """你是一个智能路由助手，负责判断小学生的学习问题属于哪个类别。

分类规则：
- essay（作文辅导）：涉及写作、作文题目、文章结构、好词好句
- english（英语辅导）：涉及英语单词、例句、发音、记忆方法
- math（数学辅导）：涉及数学题目理解、应用题、计算题题意
- mistake（错题分析）：涉及做错的题目、错误原因分析

请根据用户输入，准确判断属于哪个类别。"""


async def route_intent(user_message: str) -> RouterDecision:
    return await parse_structured(
        model_role="router",
        system_prompt=ROUTER_SYSTEM_PROMPT,
        user_message=f"请分类这个问题：{user_message}",
        response_model=RouterDecision,
        max_tokens=1024,
    )
