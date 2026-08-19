from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, llm_ready

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


class LLMError(RuntimeError):
    pass


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8").strip()


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not llm_ready():
        raise LLMError("Missing OPENAI_API_KEY. Add it to .env to enable AI features.")
    kwargs: dict[str, str] = {"api_key": OPENAI_API_KEY}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    return OpenAI(**kwargs)


def complete(
    *,
    system: str,
    user: str,
    temperature: float = 0.4,
    json_mode: bool = False,
) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    request: dict = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        request["response_format"] = {"type": "json_object"}

    response = _client().chat.completions.create(**request)
    content = response.choices[0].message.content
    if not content:
        raise LLMError("The model returned an empty response.")
    return content.strip()
