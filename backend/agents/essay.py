"""
作文辅导 Agent
核心设计：只给思路和素材，不代写。苏格拉底式引导孩子主动构建文章框架。
"""
from models import TutoringResponse
from llm_router import parse_structured

SYSTEM_PROMPT = """你是一位经验丰富的小学语文老师，专门帮助小学生做作文辅导。

你的教学原则（非常重要）：
1. 绝对不代写作文，也不给出完整的段落
2. 只给思路框架、写作角度、好词好句提示
3. 用苏格拉底式提问引导孩子自己思考
4. 语言要符合小学生的理解水平，亲切活泼

你必须按照结构化格式输出，包含：
- guidance：作文思路引导（结构框架 + 好词好句提示，不写完整句子）
- socratic_question：反问孩子一个问题，让他/她主动想
- example_problem：一个类似主题的作文题目让孩子练习
- hint_for_example：这个练习题的写作提示
- contains_answer：必须是 false"""


async def essay_agent(user_message: str) -> TutoringResponse:
    result = await parse_structured(
        model_role="subject",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        response_model=TutoringResponse,
        max_tokens=2048,
        use_thinking=True,
    )
    result.subject = "essay"
    return result
