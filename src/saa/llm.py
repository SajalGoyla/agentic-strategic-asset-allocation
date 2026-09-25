"""Anthropic client wrapper: model routing, structured outputs, retries and cost accounting.

Every LLM call in the pipeline goes through ``LlmClient.judge``, which constrains the response
to one of the judgment models in ``saa.contracts`` and returns it already validated, together
with a ``ModelCall`` record for ``header.model_calls``.

Three things this exists to guarantee:

* **The model cannot invent its own output shape.** ``messages.parse(output_format=...)`` is
  given a judgment model, so a response that does not fit the contract never reaches an agent.
* **Contract validators are enforced, not merely hoped for.** The API validates against the
  JSON Schema, but our own ``model_validator`` rules -- a CMA estimate inside the candidate
  range, a rationale per dimension -- are Python. When one fails, the error is fed back to the
  model and it retries.
* **Spend is attributable.** Every call records tokens and cost against the agent that made it,
  so the project's $210-290 budget can be tracked per stage rather than guessed at.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import ValidationError

from saa.contracts.base import Contract, ModelCall, Tier

if TYPE_CHECKING:
    from anthropic import Anthropic

log = logging.getLogger(__name__)

JudgmentT = TypeVar("JudgmentT", bound=Contract)

# Project plan §6 routes nuanced judgment to a flagship model and routine formatting to a
# cheaper one. Prices are USD per million tokens, for the budget arithmetic only.
MODELS: dict[Tier, str] = {
    Tier.FLAGSHIP: "claude-opus-5",
    Tier.LOW_COST: "claude-sonnet-5",
}

PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}

# Cached input is billed at roughly a tenth of the input rate. Used for the budget estimate
# only; the authoritative number is whatever the invoice says.
CACHE_READ_DISCOUNT = 0.1

DEFAULT_MAX_TOKENS = 16_000
DEFAULT_RETRIES = 2


def estimate_cost_usd(model: str, usage: Any) -> float | None:
    """Cost of one call from its usage block, or None for an unpriced model."""
    rates = PRICING.get(model)
    if rates is None:
        return None
    input_rate, output_rate = rates
    fresh = getattr(usage, "input_tokens", 0) or 0
    cached = getattr(usage, "cache_read_input_tokens", 0) or 0
    written = getattr(usage, "cache_creation_input_tokens", 0) or 0
    output = getattr(usage, "output_tokens", 0) or 0
    million = 1_000_000
    return (
        fresh * input_rate
        + cached * input_rate * CACHE_READ_DISCOUNT
        + written * input_rate * 1.25
        + output * output_rate
    ) / million


class BudgetExceeded(RuntimeError):
    """Raised when a run would pass its spend cap. The pipeline stops rather than overspends."""


@dataclass
class Budget:
    """Run-level spend tracking. ``cap_usd=None`` tracks without enforcing."""

    cap_usd: float | None = None
    warn_at: float = 0.8
    spent_usd: float = 0.0
    calls: int = 0
    _warned: bool = field(default=False, repr=False)

    def record(self, call: ModelCall) -> None:
        self.spent_usd += call.cost_usd or 0.0
        self.calls += 1
        if self.cap_usd is None:
            return
        if not self._warned and self.spent_usd >= self.cap_usd * self.warn_at:
            self._warned = True
            log.warning("run has spent $%.2f of its $%.2f cap", self.spent_usd, self.cap_usd)

    def check(self) -> None:
        """Called before starting a stage, so a run stops at a boundary rather than mid-fan-out."""
        if self.cap_usd is not None and self.spent_usd >= self.cap_usd:
            raise BudgetExceeded(
                f"run has spent ${self.spent_usd:.2f}, at or over its ${self.cap_usd:.2f} cap"
            )


@dataclass
class Judgment:
    """A validated judgment plus the call that produced it."""

    value: Any
    call: ModelCall
    attempts: int


class LlmClient:
    """Thin wrapper over the Messages API. Inject a fake ``client`` in tests."""

    def __init__(
        self,
        client: Anthropic | None = None,
        *,
        budget: Budget | None = None,
        max_retries: int = DEFAULT_RETRIES,
        models: dict[Tier, str] | None = None,
    ):
        self._client = client
        self.budget = budget or Budget()
        self.max_retries = max_retries
        self.models = models or dict(MODELS)

    @property
    def client(self) -> Anthropic:
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - dependency is declared
                raise RuntimeError("the `anthropic` package is required for LLM calls") from exc
            if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")):
                raise RuntimeError(
                    "no Anthropic credentials found; set ANTHROPIC_API_KEY in .env "
                    "or run `ant auth login`"
                )
            self._client = anthropic.Anthropic()
        return self._client

    def judge(
        self,
        output_format: type[JudgmentT],
        *,
        system: str,
        prompt: str,
        tier: Tier = Tier.FLAGSHIP,
        effort: str = "high",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        cache_system: bool = True,
    ) -> Judgment:
        """Ask for one judgment, constrained to ``output_format`` and validated on return.

        ``system`` is cached: agents that fan out over 18 asset classes or 21 portfolios resend
        the same instructions and shared context every time, and cached input costs about a
        tenth of fresh input.
        """
        self.budget.check()
        model = self.models[tier]

        system_blocks: list[dict[str, Any]] = [{"type": "text", "text": system}]
        if cache_system:
            system_blocks[0]["cache_control"] = {"type": "ephemeral"}

        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 2):
            response = self.client.messages.parse(
                model=model,
                max_tokens=max_tokens,
                system=system_blocks,
                messages=messages,
                output_format=output_format,
                thinking={"type": "adaptive"},
                output_config={"effort": effort},
            )
            call = ModelCall(
                model=model,
                tier=tier,
                effort=effort,
                input_tokens=getattr(response.usage, "input_tokens", 0) or 0,
                output_tokens=getattr(response.usage, "output_tokens", 0) or 0,
                cache_read_tokens=getattr(response.usage, "cache_read_input_tokens", 0) or 0,
                cost_usd=estimate_cost_usd(model, response.usage),
            )
            self.budget.record(call)

            if response.stop_reason == "refusal":
                raise RuntimeError(
                    f"{model} declined the request "
                    f"({getattr(response.stop_details, 'category', 'unknown')})"
                )

            parsed = response.parsed_output
            try:
                # The API validates the schema; this re-runs our own model_validator rules,
                # which are Python and invisible to it.
                value = output_format.model_validate(
                    parsed if isinstance(parsed, dict) else parsed.model_dump()
                )
            except ValidationError as exc:
                last_error = exc
                log.warning(
                    "%s output failed contract validation on attempt %d/%d",
                    output_format.__name__,
                    attempt,
                    self.max_retries + 1,
                )
                if attempt > self.max_retries:
                    break
                messages += [
                    {"role": "assistant", "content": _as_text(parsed)},
                    {
                        "role": "user",
                        "content": (
                            "That response did not satisfy the output contract:\n\n"
                            f"{exc}\n\nReturn a corrected response."
                        ),
                    },
                ]
                continue

            return Judgment(value=value, call=call, attempts=attempt)

        raise ValueError(
            f"{output_format.__name__} did not satisfy its contract after "
            f"{self.max_retries + 1} attempts: {last_error}"
        ) from last_error


def _as_text(parsed: Any) -> str:
    if hasattr(parsed, "model_dump_json"):
        return parsed.model_dump_json()
    import json

    return json.dumps(parsed, default=str)
