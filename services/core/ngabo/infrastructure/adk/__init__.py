"""ADK/Gemini runtime adapter for the Issue #49 capability spike.

This package is the sanctioned outer-dependency home for ``google.adk`` and
``google.genai``. It implements a thin spike runtime that proves the
non-interactive event invocation path, graph parallel/join, a real ADK LLM
agent with structured output, and the deterministic verifier / bounded-repair
boundary. Domain and application layers never import from here.
"""

from ngabo.infrastructure.adk.spike_adapter import SpikeRunResult, run_spike

__all__ = ["SpikeRunResult", "run_spike"]
