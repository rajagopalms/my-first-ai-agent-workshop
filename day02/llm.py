"""Shared model helper for day 2.

Same idea as day01/hello_model.py, but as a function the other day 2 scripts
can import. It reads the three MODEL_* values from .env, so it works with
Ollama now and with Azure AI Foundry from day 4 without code changes.
"""

import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass
class Reply:
    text: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str  # "stop" = model finished; "length" = cut off by max_tokens

    def usage_line(self) -> str:
        total = self.prompt_tokens + self.completion_tokens
        return (
            f"tokens in: {self.prompt_tokens} | out: {self.completion_tokens} "
            f"| total: {total} | finish: {self.finish_reason}"
        )


_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        endpoint = os.getenv("MODEL_ENDPOINT")
        api_key = os.getenv("MODEL_API_KEY")
        if not (endpoint and api_key and os.getenv("MODEL_NAME")):
            sys.exit("Set MODEL_ENDPOINT, MODEL_NAME and MODEL_API_KEY in .env (see .env.example).")
        _client = OpenAI(base_url=endpoint, api_key=api_key)
    return _client


def chat(
    system: str, user: str, temperature: float = 0.2, max_tokens: int = 400, json_mode: bool = False
) -> Reply:
    """Send one system message and one user message, return the reply and its usage.

    json_mode=True makes the model return valid JSON (it cannot emit a token that
    breaks the syntax). It does not check the keys: validate those yourself.
    """
    kwargs = {
        "model": os.getenv("MODEL_NAME"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = _get_client().chat.completions.create(**kwargs)
    choice = response.choices[0]
    return Reply(
        text=(choice.message.content or "").strip(),
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        finish_reason=choice.finish_reason,
    )
