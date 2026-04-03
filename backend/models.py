"""
Pydantic schemas for Structured Output — 护栏设计的核心
通过 Function Calling 从协议层强制约束输出格式，阻断 AI 直接给答案
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class RouterDecision(BaseModel):
    """Router Agent 的意图分类输出"""
    subject: Literal["essay", "english", "math", "mistake"] = Field(
        description="判断用户输入属于哪个学科辅导类型"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="分类置信度 0-1")
    reason: str = Field(description="判断理由（用于 debug 和日志）")


class TutoringResponse(BaseModel):
    """
    学科 Agent 的结构化输出 — 教育护栏的核心设计

    设计原则：
    1. guidance 只包含思路引导，绝不包含完整答案
    2. socratic_question 强制要求每次回答都要反问孩子
    3. example_problem 提供类似练习，间隔重复巩固
    4. contains_answer 是护栏验证字段，生产中应始终为 False
    """
    subject: Literal["essay", "english", "math", "mistake"] = Field(
        description="辅导学科类型"
    )
    guidance: str = Field(
        description="给孩子的引导内容。只给思路、好词、提示，不能给完整答案或代写"
    )
    socratic_question: str = Field(
        description="苏格拉底式反问：引导孩子主动思考的问题，帮助检验理解"
    )
    example_problem: str = Field(
        description="一道类似的练习题，让孩子独立尝试，不包含答案"
    )
    hint_for_example: str = Field(
        description="例题的解题思路提示，不是答案"
    )
    contains_answer: bool = Field(
        default=False,
        description="护栏字段：guidance 中是否包含了直接答案。应始终为 False"
    )

    @model_validator(mode="after")
    def validate_no_direct_answer(self) -> TutoringResponse:
        """后验证：如果 contains_answer=True，说明 Prompt 设计有问题"""
        if self.contains_answer:
            raise ValueError(
                "护栏触发：AI 尝试给出直接答案。请检查 Prompt 设计。"
            )
        return self


class EvaluationResponse(BaseModel):
    """评价孩子对反问的回答"""
    is_correct_thinking: bool = Field(description="孩子的思路方向是否正确")
    encouragement: str = Field(description="鼓励性评价，即使答错也要正向引导")
    correction_hint: Optional[str] = Field(
        default=None,
        description="如果思路有偏差，给一个纠正的提示（不是答案）"
    )
    next_step: str = Field(description="告诉孩子下一步可以怎么做")


class ChatMessage(BaseModel):
    """前端发送的对话消息"""
    message: str = Field(min_length=1, max_length=500)
    subject: Optional[Literal["essay", "english", "math", "mistake"]] = None
    session_id: Optional[str] = None
    is_answer_to_socratic: bool = Field(
        default=False,
        description="是否是孩子在回答苏格拉底反问"
    )
    original_guidance: Optional[str] = None


class EvaluateRequest(BaseModel):
    """评价孩子回答的请求"""
    original_problem: str
    student_answer: str
    subject: Literal["essay", "english", "math", "mistake"]
    session_id: Optional[str] = None
