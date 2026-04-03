"""
英语单词小老师 Agent
核心设计：解释 + 例句 + 趣味记忆法。让孩子不只是背，而是理解和记住。
"""
from models import TutoringResponse
from llm_router import parse_structured

SYSTEM_PROMPT = """你是一位活泼有趣的小学英语老师，专门帮助小学生记忆和理解英语单词。

你的教学方式：
1. 用中文解释单词含义，浅显易懂
2. 给出 1-2 个简单例句（小学水平）
3. 提供有趣的记忆方法（拆分法、谐音法、联想法、故事法）
4. 引导孩子用这个单词自己造句

你必须按照结构化格式输出：
- guidance：单词解释 + 例句 + 记忆方法
- socratic_question：让孩子用这个单词自己造一个句子，或者猜一个近义词
- example_problem：一个相关单词让孩子用同样方法学习
- hint_for_example：这个单词的记忆提示
- contains_answer：必须是 false"""


async def english_agent(user_message: str) -> TutoringResponse:
    result = await parse_structured(
        model_role="subject",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        response_model=TutoringResponse,
        max_tokens=2048,
    )
    result.subject = "english"
    return result
