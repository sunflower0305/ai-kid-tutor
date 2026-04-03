"""
LLM 路由模块 — 统一支持 Claude（Anthropic）和国内模型（Qwen/DeepSeek/GLM/Doubao/MiniMax）

通过环境变量 LLM_PROVIDER 切换：
  - claude   → Anthropic SDK，支持 Thinking，支持本地代理（ANTHROPIC_BASE_URL）
  - qwen     → DashScope OpenAI 兼容接口（DASHSCOPE_API_KEY）
  - deepseek → DeepSeek API（DEEPSEEK_API_KEY）
  - glm      → 智谱 AI（GLM_API_KEY）
  - doubao   → 字节跳动火山引擎（DOUBAO_API_KEY + DOUBAO_MODEL）
  - minimax  → MiniMax API（MINIMAX_API_KEY）
"""
from __future__ import annotations

import json
import os
from typing import Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# ─── 模型映射 ─────────────────────────────────────────────────────────────────
# role: "router" | "subject" | "evaluate"

_MODEL_MAP: dict[str, dict[str, str]] = {
    "claude": {
        "router":   "claude-haiku-4-5",
        "subject":  "claude-opus-4-6",
        "evaluate": "claude-sonnet-4-6",
    },
    "qwen": {
        "router":   "qwen-turbo",
        "subject":  "qwen-plus",
        "evaluate": "qwen-plus",
    },
    "deepseek": {
        "router":   "deepseek-chat",
        "subject":  "deepseek-chat",
        "evaluate": "deepseek-chat",
    },
    "glm": {
        "router":   "glm-4-flash",
        "subject":  "glm-4-plus",
        "evaluate": "glm-4",
    },
    "doubao": {
        "router":   "",  # 从 DOUBAO_MODEL 读取
        "subject":  "",
        "evaluate": "",
    },
    "minimax": {
        "router":   "MiniMax-M2.7-highspeed",
        "subject":  "MiniMax-M2.7-highspeed",
        "evaluate": "MiniMax-M2.7-highspeed",
    },
}

# OpenAI 兼容接口的 base_url
_BASE_URL_MAP = {
    "qwen":     "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "glm":      "https://open.bigmodel.cn/api/paas/v4/",
    "doubao":   lambda: os.environ.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    "minimax":  "https://api.minimax.chat/v1",
}

# API Key 来源
_API_KEY_MAP = {
    "qwen":     lambda: os.environ.get("DASHSCOPE_API_KEY", ""),
    "deepseek": lambda: os.environ.get("DEEPSEEK_API_KEY", ""),
    "glm":      lambda: os.environ.get("GLM_API_KEY", ""),
    "doubao":   lambda: os.environ.get("DOUBAO_API_KEY", ""),
    "minimax":  lambda: os.environ.get("MINIMAX_API_KEY", ""),
}


# ─── 公共接口 ─────────────────────────────────────────────────────────────────

async def parse_structured(
    model_role: str,
    system_prompt: str,
    user_message: str,
    response_model: Type[T],
    max_tokens: int = 2048,
    use_thinking: bool = False,
) -> T:
    """
    统一结构化输出接口。

    Args:
        model_role:     "router" | "subject" | "evaluate"
        system_prompt:  系统提示词
        user_message:   用户输入
        response_model: Pydantic 输出模型类
        max_tokens:     最大输出 token 数
        use_thinking:   是否启用推理（仅 Claude 生效）
    """
    provider = os.environ.get("LLM_PROVIDER", "claude").lower()

    if provider == "claude":
        return await _call_anthropic(
            model_role, system_prompt, user_message,
            response_model, max_tokens, use_thinking,
        )
    elif provider in _API_KEY_MAP:
        return await _call_openai_compatible(
            provider, model_role, system_prompt, user_message,
            response_model, max_tokens,
        )
    else:
        raise ValueError(f"不支持的 LLM_PROVIDER: {provider}，可选: claude/qwen/deepseek/glm/doubao")


def get_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "claude").lower()


# ─── Anthropic 实现 ───────────────────────────────────────────────────────────

async def _call_anthropic(
    model_role: str,
    system_prompt: str,
    user_message: str,
    response_model: Type[T],
    max_tokens: int,
    use_thinking: bool,
) -> T:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_url = os.environ.get("ANTHROPIC_BASE_URL") or None  # 本地代理支持

    client = anthropic.AsyncAnthropic(api_key=api_key, base_url=base_url)
    model = _MODEL_MAP["claude"][model_role]

    kwargs: dict = dict(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        output_format=response_model,
    )
    if use_thinking:
        kwargs["thinking"] = {"type": "adaptive"}

    response = await client.messages.parse(**kwargs)
    return response.parsed_output


# ─── OpenAI 兼容实现 ──────────────────────────────────────────────────────────

async def _call_openai_compatible(
    provider: str,
    model_role: str,
    system_prompt: str,
    user_message: str,
    response_model: Type[T],
    max_tokens: int,
) -> T:
    from openai import AsyncOpenAI

    api_key = _API_KEY_MAP[provider]()
    base_url_entry = _BASE_URL_MAP[provider]
    base_url = base_url_entry() if callable(base_url_entry) else base_url_entry

    # doubao 模型从 env 读取
    if provider == "doubao":
        model = os.environ.get("DOUBAO_MODEL", "")
        if not model:
            raise ValueError("使用 doubao 时请设置 DOUBAO_MODEL 环境变量")
    else:
        model = _MODEL_MAP[provider][model_role]

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # 将 Pydantic schema 注入 system prompt，引导输出 JSON
    schema = response_model.model_json_schema()
    json_instruction = (
        f"\n\n【重要】你必须只输出一个合法的 JSON 对象，格式严格遵循以下 schema，不得输出任何额外文字：\n"
        f"```json\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n```"
    )

    # minimax 不支持 response_format 参数，其余支持 json_object 强制模式
    extra: dict = {} if provider == "minimax" else {"response_format": {"type": "json_object"}}

    completion = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt + json_instruction},
            {"role": "user", "content": user_message},
        ],
        **extra,
    )

    raw = completion.choices[0].message.content or ""
    # 剥掉 <think>...</think> 推理块（MiniMax/DeepSeek 推理模型会输出）
    import re
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    # 提取第一个 { 到最后一个 } 之间的内容（最健壮的 JSON 提取方式）
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]
    raw = raw or "{}"
    # 国内模型有时会错误地把 contains_answer 设为 true，强制覆盖避免误触发护栏
    data = json.loads(raw)
    if "contains_answer" in data:
        data["contains_answer"] = False
    return response_model.model_validate(data)
