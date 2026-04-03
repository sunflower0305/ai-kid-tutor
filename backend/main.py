"""
AI-KID-TUTOR FastAPI 后端服务

架构亮点：
- Multi-Agent：Router Agent + 4 个学科 Subject Agent
- Structured Output：Pydantic 护栏，协议层阻断 AI 直接给答案
- 苏格拉底教学法：每次响应都包含反问 + 例题
- 支持多模型：claude（默认）/ doubao（国内兜底）
"""
from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from agents import AGENT_MAP, route_intent
from agents.mistakes import evaluate_student_answer
from models import ChatMessage, EvaluateRequest, TutoringResponse

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时验证 API Key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  警告：未设置 ANTHROPIC_API_KEY，请检查 .env 文件")
    else:
        print(f"✅ Claude API Key 已加载（前8位：{api_key[:8]}...）")
    yield


app = FastAPI(
    title="AI-KID-TUTOR",
    description="面向小学生的 AI 学习辅助工具，基于 Multi-Agent + Structured Output 架构",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置（支持前端本地开发）
origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500").split(",")
origins.extend(["http://localhost:8080", "http://127.0.0.1:8080", "null"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── API 路由 ────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "provider": os.environ.get("LLM_PROVIDER", "claude"),
        "version": "1.0.0",
    }


@app.post("/api/tutor")
async def tutor(request: ChatMessage):
    """
    主辅导接口 — SSE 流式返回

    流程：
    1. Router Agent 判断学科意图（Structured Output）
    2. 路由到对应 Subject Agent
    3. Subject Agent 返回：引导 + 反问 + 例题（Structured Output 护栏）
    4. 以 SSE 格式流式返回给前端
    """
    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Step 1: 如果没有指定学科，用 Router Agent 自动判断
            subject = request.subject
            if not subject:
                yield _sse_event("status", {"message": "正在分析问题类型..."})
                decision = await route_intent(request.message)
                subject = decision.subject
                yield _sse_event("routed", {
                    "subject": subject,
                    "confidence": decision.confidence,
                    "reason": decision.reason,
                })

            yield _sse_event("status", {"message": "老师正在思考..."})

            # Step 2: 调用对应的 Subject Agent
            agent_fn = AGENT_MAP.get(subject)
            if not agent_fn:
                yield _sse_event("error", {"message": f"未知学科：{subject}"})
                return

            response: TutoringResponse = await agent_fn(request.message)

            # Step 3: 返回结构化结果
            yield _sse_event("response", {
                "subject": response.subject,
                "guidance": response.guidance,
                "socratic_question": response.socratic_question,
                "example_problem": response.example_problem,
                "hint_for_example": response.hint_for_example,
                "session_id": request.session_id or str(uuid.uuid4()),
            })

            yield _sse_event("done", {})

        except ValueError as e:
            if "护栏触发" in str(e):
                yield _sse_event("guardrail_triggered", {
                    "message": "检测到不当输出，已自动拦截",
                    "detail": str(e),
                })
            else:
                yield _sse_event("error", {"message": f"服务暂时不可用：{str(e)}"})
        except Exception as e:
            yield _sse_event("error", {"message": f"服务暂时不可用：{str(e)}"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/evaluate")
async def evaluate(request: EvaluateRequest):
    """
    评价孩子对苏格拉底反问的回答
    使用 claude-sonnet-4-6，平衡速度和质量
    """
    try:
        result = await evaluate_student_answer(
            original_problem=request.original_problem,
            student_answer=request.student_answer,
            subject=request.subject,
        )
        return {
            "is_correct_thinking": result.is_correct_thinking,
            "encouragement": result.encouragement,
            "correction_hint": result.correction_hint,
            "next_step": result.next_step,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── 静态文件（前端） ────────────────────────────────────────────────────────

frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def _sse_event(event_type: str, data: dict) -> str:
    """格式化 Server-Sent Events 消息"""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
