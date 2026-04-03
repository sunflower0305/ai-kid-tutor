from .router import route_intent
from .essay import essay_agent
from .english import english_agent
from .math import math_agent
from .mistakes import mistakes_agent

AGENT_MAP = {
    "essay": essay_agent,
    "english": english_agent,
    "math": math_agent,
    "mistake": mistakes_agent,
}

__all__ = [
    "route_intent",
    "essay_agent",
    "english_agent",
    "math_agent",
    "mistakes_agent",
    "AGENT_MAP",
]
