"""Deterministic fake ADK LLM for offline spike tests (#49).

``SpikeFakeLlm`` subclasses ADK's ``BaseLlm`` and yields canned
``LlmResponse`` content per ``generate_content_async`` call, so the same ADK
agent/Workflow graph can be exercised deterministically in CI without paid
model calls. It records every ``LlmRequest`` it receives so tests can assert
that a bounded repair was actually given the structured verifier errors (a
"model self-verification is not used" boundary proof).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from google.adk.models import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import PrivateAttr


class SpikeFakeLlm(BaseLlm):
    """Deterministic canned-response ADK LLM bound to an Agent's ``model``."""

    model: str = "fake-model"

    _responses: list[str] = PrivateAttr(default_factory=list)
    _requests: list[LlmRequest] = PrivateAttr(default_factory=list)
    _call_count: int = PrivateAttr(default=0)

    def __init__(self, responses: list[str], model: str = "fake-model") -> None:
        super().__init__(model=model)
        self._responses = list(responses)

    @property
    def call_count(self) -> int:
        """Number of model turns requested so far."""
        return self._call_count

    @property
    def requests(self) -> tuple[LlmRequest, ...]:
        """Immutable snapshot of every request received."""
        return tuple(self._requests)

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        del stream
        self._call_count += 1
        self._requests.append(llm_request)
        text = self._responses[0] if self._responses else "{}"
        self._responses = self._responses[1:]
        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text=text)]),
            model_version="fake-model",
            turn_complete=True,
        )
