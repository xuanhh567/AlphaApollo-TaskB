"""Small OpenAI-compatible chat completion client for evaluation runners."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatCompletionResult:
    """Text returned by an API model plus the raw response for debugging."""

    text: str
    raw: dict[str, Any]


class OpenAICompatibleChatClient:
    """Minimal client for ``/chat/completions`` compatible APIs.

    The project already has heavy local generation paths through verl/vLLM.
    This client intentionally stays dependency-light so API-based regression
    can run in the same environment without installing another SDK.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 120.0,
        retries: int = 2,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries

    @property
    def chat_completions_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return f"{self.base_url}/chat/completions"

    def generate(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        top_p: float = 1.0,
    ) -> ChatCompletionResult:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                raw = self._post_json(payload)
                return ChatCompletionResult(
                    text=_extract_assistant_text(raw),
                    raw=raw,
                )
            except Exception as exc:  # pragma: no cover - exercised in real API runs
                last_error = exc
                if attempt >= self.retries:
                    break
                time.sleep(min(2**attempt, 8))

        raise RuntimeError(f"API generation failed after {self.retries + 1} attempt(s): {last_error}")

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.chat_completions_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def _extract_assistant_text(raw: dict[str, Any]) -> str:
    choices = raw.get("choices") or []
    if not choices:
        return ""

    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str) and content:
        return content

    # Some OpenAI-compatible APIs may return native tool_calls even when the
    # prompt asks for text tags. Normalize them into the textual form accepted
    # by the Task B parser so the rest of the environment can stay unchanged.
    tool_calls = message.get("tool_calls")
    if tool_calls:
        normalized = []
        for tool_call in tool_calls:
            function = tool_call.get("function") or {}
            normalized.append(
                {
                    "name": function.get("name"),
                    "arguments": function.get("arguments") or {},
                }
            )
        return "<tool_calls>" + json.dumps(normalized, ensure_ascii=False) + "</tool_calls>"

    return ""
