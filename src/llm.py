"""OpenAI model construction — one place, so agent.py and brief.py can't drift apart.

Two things this centralises, both learned the hard way against the live API:

TEMPERATURE
    gpt-5.x reasoning models reject any temperature other than the default:
      "Unsupported value: 'temperature' does not support 0.2 with this model."
    So temperature is omitted unless OPENAI_TEMPERATURE is explicitly set, which keeps
    older models (gpt-4o, gpt-4.1) configurable without breaking the new ones.

STRUCTURED OUTPUT
    Agent.structured_output() is deprecated. The current form passes
    structured_output_model into the invocation and reads .structured_output off the
    AgentResult. ask() wraps that so call sites don't have to care when it changes again.
"""

from __future__ import annotations

import os
from typing import TypeVar

from pydantic import BaseModel

import env  # noqa: F401  — loads .env and fixes the macOS CA bundle

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "gpt-5.5"


def model_id() -> str:
    return os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL


def build_model():
    """An OpenAIModel configured from the environment."""
    from strands.models.openai import OpenAIModel

    params = {}
    if (temp := os.environ.get("OPENAI_TEMPERATURE")) is not None:
        params["temperature"] = float(temp)

    return OpenAIModel(
        client_args={"api_key": os.environ["OPENAI_API_KEY"]},
        model_id=model_id(),
        **({"params": params} if params else {}),
    )


def build_agent(system_prompt: str, tools: list | None = None):
    from strands import Agent

    return Agent(model=build_model(), system_prompt=system_prompt, tools=tools or [])


def ask(agent, prompt: str, schema: type[T]) -> T:
    """Invoke an agent and get back a validated Pydantic object."""
    result = agent(prompt, structured_output_model=schema)
    out = getattr(result, "structured_output", None)
    if out is None:
        raise RuntimeError(
            f"no structured_output on {type(result).__name__}; "
            f"attrs: {[a for a in dir(result) if not a.startswith('_')][:15]}"
        )
    return out
