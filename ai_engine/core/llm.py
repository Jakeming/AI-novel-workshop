"""
llm.py — Deep LLM client module.

Interface: llm.call(task_name, ctx) -> dict
Hides: prompt templates, retry, fallback, token tracking, structured output parsing.
"""
import json, time, logging, os
from functools import lru_cache
from typing import Any

import openai  # pip install openai

_log = logging.getLogger(__name__)

# --- prompt registry — one entry per task task_name ---
_PROMPTS = {}

def register_prompt(name: str):
    """Decorator: register prompt builder for task `name`."""
    def wrap(fn):
        _PROMPTS[name] = fn
        return fn
    return wrap

def _default_client():
    return openai.OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    )

class LLM:
    """Deep module: one public method, hides all LLM plumbing."""

    def __init__(self, client=None, model: str | None = None):
        self._client = client or _default_client()
        self._model = model or os.getenv("LLM_MODEL", "gpt-4o")
        self._stats = {"calls": 0, "tokens": 0, "errors": 0}

    def call(self, task_name: str, ctx: dict[str, Any], **kw) -> dict[str, Any]:
        """
        Single entry point.
        task_name — matches a registered prompt builder.
        ctx — vars injected into prompt template.
        Returns parsed JSON dict.
        """
        builder = _PROMPTS.get(task_name)
        if not builder:
            raise KeyError(f"Unknown task: {task_name}. Registered: {list(_PROMPTS)}")

        prompt = builder(ctx)
        raw = self._chat(prompt, **kw)
        return self._parse(task_name, raw)

    # --- internals ---

    def _chat(self, prompt: str, max_retries=2, **kw) -> str:
        last_err = None
        for attempt in range(max_retries + 1):
            try:
                resp = self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=kw.get("temperature", 0.3),
                    response_format={"type": "json_object"},
                )
                self._stats["calls"] += 1
                usage = resp.usage
                if usage:
                    self._stats["tokens"] += usage.total_tokens
                return resp.choices[0].message.content
            except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as e:
                _log.warning("LLM attempt %d failed: %s", attempt + 1, e)
                last_err = e
                if attempt < max_retries:
                    time.sleep(2 ** attempt)  # exponential backoff
        self._stats["errors"] += 1
        raise last_err or RuntimeError("LLM call failed")

    def _parse(self, task_name: str, raw: str) -> dict:
        """Extract JSON from LLM output (may have markdown fences)."""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            _log.error("JSON parse failed for %s. Raw: %.200s", task_name, raw)
            # fallback: return raw under "error" key so caller can decide
            return {"_parse_error": True, "raw": raw}

    def stats(self) -> dict:
        return {**self._stats}

    def reset_stats(self):
        self._stats = {"calls": 0, "tokens": 0, "errors": 0}

# --- convenience shortcut (lazy init, callable) ---
def _call_lazy(task_name: str, ctx: dict, **kw) -> dict:
    """Lazy LLM shortcut — defers client init until first call."""
    return LLM().call(task_name, ctx, **kw)
