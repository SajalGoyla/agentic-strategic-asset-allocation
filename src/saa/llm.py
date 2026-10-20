"""LLM client wrapper: model routing, structured outputs, retries and cost accounting.

Every LLM call in the pipeline goes through ``LlmClient.judge``, which constrains the response
to one of the judgment models in ``saa.contracts`` and returns it already validated, together
with a ``ModelCall`` record for ``header.model_calls``.

Three things this exists to guarantee:

* **The model cannot invent its own output shape.** The judgment model's JSON Schema is handed
  to the API, so a response that does not fit the contract never reaches an agent.
* **Contract validators are enforced, not merely hoped for.** The API validates against the
  JSON Schema, but our own ``model_validator`` rules -- a CMA estimate inside the candidate
  range, a rationale per dimension -- are Python. When one fails, the error is fed back to the
  model and it retries.
* **Spend is attributable.** Every call records tokens and cost against the agent that made it,
  so the project's $210-290 budget can be tracked per stage rather than guessed at.

Two providers, chosen by ``SAA_LLM_PROVIDER`` (default ``anthropic``):

* ``anthropic`` -- the Messages API with ``messages.parse(output_format=...)``, adaptive
  thinking, effort and prompt caching. The paid runs.
* ``openrouter`` -- OpenRouter's OpenAI-compatible chat API with ``response_format:
  json_schema`` in strict mode, routed only to a provider that supports it. For dry runs on
  free models, which check the machinery rather than the quality of the judgments. Free models
  are rate-limited (20 requests a minute; 50 a day, or 1,000 a day once $10 of credit has been
  bought), so calls are paced and a 429 is retried with backoff.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import ValidationError

from saa.contracts.base import Contract, ModelCall, Tier

if TYPE_CHECKING:
    from anthropic import Anthropic

log = logging.getLogger(__name__)

JudgmentT = TypeVar("JudgmentT", bound=Contract)

ANTHROPIC = "anthropic"
OPENROUTER = "openrouter"
PROVIDERS = (ANTHROPIC, OPENROUTER)

# Project plan §6 routes nuanced judgment to a flagship model and routine formatting to a
# cheaper one. Prices are USD per million tokens, for the budget arithmetic only.
MODELS: dict[Tier, str] = {
    Tier.FLAGSHIP: "claude-opus-5",
    Tier.LOW_COST: "claude-sonnet-5",
}

# Dry runs: one free model for both tiers, so a failure points at the machinery rather than at
# a difference between two models. Overridden by SAA_OPENROUTER_MODEL (both tiers) or
# SAA_OPENROUTER_MODEL_FLAGSHIP / SAA_OPENROUTER_MODEL_LOW_COST.
OPENROUTER_DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# OpenRouter's free-model limit is 20 requests a minute; pace a little under it.
OPENROUTER_FREE_RPM = 18
OPENROUTER_TIMEOUT_S = 600
OPENROUTER_RATE_RETRIES = 6

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


class QuotaExhausted(RuntimeError):
    """Raised when a provider's daily request quota is used up: retrying cannot help today."""


@dataclass
class Budget:
    """Run-level spend tracking. ``cap_usd=None`` tracks without enforcing."""

    cap_usd: float | None = None
    warn_at: float = 0.8
    spent_usd: float = 0.0
    calls: int = 0
    _warned: bool = field(default=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, call: ModelCall) -> None:
        with self._lock:
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


@dataclass
class _Completion:
    """What one provider call returned, in provider-neutral form."""

    parsed: Any  # a dict or a pydantic model, or None if the text was not JSON
    text: str  # the raw response, fed back to the model on a retry
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cost_usd: float | None
    refusal: str | None = None  # why the provider declined, if it did
    parse_error: str | None = None


class _Pacer:
    """Spaces calls at least ``60 / rpm`` seconds apart, across threads."""

    def __init__(self, rpm: float, sleep: Callable[[float], None] = time.sleep):
        self.interval = 60.0 / rpm if rpm > 0 else 0.0
        self._sleep = sleep
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + self.interval
        if start > now:
            self._sleep(start - now)


# Keywords some providers' grammar engines reject outright (NVIDIA: "Unimplemented keys:
# ["propertyNames"]"). Dropping them only loosens the hint; the contract still validates
# every reply and feeds a violation back, so a bad key is caught all the same.
_UNSUPPORTED_KEYWORDS = frozenset({"propertyNames"})


def _drop_unsupported(node: Any) -> Any:
    if isinstance(node, dict):
        return {
            key: value if key in ("enum", "const", "default") else _drop_unsupported(value)
            for key, value in node.items()
            if key not in _UNSUPPORTED_KEYWORDS
        }
    if isinstance(node, list):
        return [_drop_unsupported(item) for item in node]
    return node


def _strict_schema(output_format: type[Contract]) -> dict[str, Any]:
    from saa.contracts.registry import _require_all_properties

    return _drop_unsupported(_require_all_properties(output_format.model_json_schema()))


_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


def _parse_json(text: str) -> tuple[Any, str | None]:
    """The JSON object in ``text``, tolerating a markdown fence; or the error."""
    match = _FENCE.match(text or "")
    body = match.group(1) if match else (text or "")
    try:
        return json.loads(body), None
    except json.JSONDecodeError as exc:
        start, end = body.find("{"), body.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(body[start : end + 1]), None
            except json.JSONDecodeError:
                pass
        return None, f"response was not valid JSON ({exc})"


def resolve_provider(provider: str | None = None) -> str:
    chosen = (provider or os.getenv("SAA_LLM_PROVIDER") or ANTHROPIC).strip().lower()
    if chosen not in PROVIDERS:
        raise ValueError(f"unknown LLM provider {chosen!r}; choose one of {PROVIDERS}")
    return chosen


def openrouter_models() -> dict[Tier, str]:
    both = os.getenv("SAA_OPENROUTER_MODEL") or OPENROUTER_DEFAULT_MODEL
    return {
        Tier.FLAGSHIP: os.getenv("SAA_OPENROUTER_MODEL_FLAGSHIP") or both,
        Tier.LOW_COST: os.getenv("SAA_OPENROUTER_MODEL_LOW_COST") or both,
    }


class LlmClient:
    """Thin wrapper over one provider's API. Inject a fake ``client`` (Anthropic) or ``http``
    (OpenRouter) in tests.

    The provider comes from ``SAA_LLM_PROVIDER`` only when nothing is injected: an injected
    ``client`` is an Anthropic client, so a `.env` set up for a dry run cannot reroute a test.
    """

    def __init__(
        self,
        client: Anthropic | None = None,
        *,
        budget: Budget | None = None,
        max_retries: int = DEFAULT_RETRIES,
        models: dict[Tier, str] | None = None,
        provider: str | None = None,
        http: Callable[..., Any] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if provider is None and client is not None:
            provider = ANTHROPIC
        if provider is None and http is not None:
            provider = OPENROUTER
        self.provider = resolve_provider(provider)
        self._client = client
        self._http = http
        self._sleep = sleep
        self.budget = budget or Budget()
        self.max_retries = max_retries
        if models is not None:
            self.models = dict(models)
        else:
            self.models = openrouter_models() if self.provider == OPENROUTER else dict(MODELS)
        rpm = float(os.getenv("SAA_OPENROUTER_RPM") or OPENROUTER_FREE_RPM)
        self._pacer = _Pacer(rpm if self.provider == OPENROUTER else 0.0, sleep)

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

        ``system`` is cached on Anthropic: agents that fan out over 18 asset classes or 15
        portfolios resend the same instructions and shared context every time, and cached
        input costs about a tenth of fresh input.
        """
        self.budget.check()
        model = self.models[tier]
        messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
        last_error: Exception | str | None = None

        for attempt in range(1, self.max_retries + 2):
            if self.provider == OPENROUTER:
                completion = self._openrouter(
                    output_format, model, system, messages, effort, max_tokens
                )
            else:
                completion = self._anthropic(
                    output_format, model, system, messages, effort, max_tokens, cache_system
                )
            call = ModelCall(
                model=model,
                tier=tier,
                effort=effort,
                input_tokens=completion.input_tokens,
                output_tokens=completion.output_tokens,
                cache_read_tokens=completion.cache_read_tokens,
                cost_usd=completion.cost_usd,
            )
            self.budget.record(call)

            if completion.refusal is not None:
                raise RuntimeError(f"{model} declined the request ({completion.refusal})")

            try:
                if completion.parsed is None:
                    raise ValueError(completion.parse_error or "empty response")
                parsed = completion.parsed
                # The API validates the schema; this re-runs our own model_validator rules,
                # which are Python and invisible to it.
                value = output_format.model_validate(
                    parsed if isinstance(parsed, dict) else parsed.model_dump()
                )
            except (ValidationError, ValueError) as exc:
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
                    {"role": "assistant", "content": completion.text or "(no content)"},
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
        ) from (last_error if isinstance(last_error, Exception) else None)

    # ------------------------------------------------------------------------- anthropic
    def _anthropic(self, output_format, model, system, messages, effort, max_tokens, cache):
        system_blocks: list[dict[str, Any]] = [{"type": "text", "text": system}]
        if cache:
            system_blocks[0]["cache_control"] = {"type": "ephemeral"}
        response = self.client.messages.parse(
            model=model,
            max_tokens=max_tokens,
            system=system_blocks,
            messages=messages,
            output_format=output_format,
            thinking={"type": "adaptive"},
            output_config={"effort": effort},
        )
        usage = response.usage
        refusal = None
        if response.stop_reason == "refusal":
            refusal = getattr(getattr(response, "stop_details", None), "category", "unknown")
        parsed = response.parsed_output
        return _Completion(
            parsed=parsed,
            text=_as_text(parsed),
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cost_usd=estimate_cost_usd(model, usage),
            refusal=refusal,
        )

    # ------------------------------------------------------------------------ openrouter
    def _post(self, payload: dict[str, Any]):
        if self._http is not None:
            return self._http(OPENROUTER_URL, payload)
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "no OpenRouter key found; set OPENROUTER_API_KEY in .env (see .env.example)"
            )
        import requests

        return requests.post(
            OPENROUTER_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "https://github.com/SajalGoyla/agentic-strategic-asset-allocation",
                "X-Title": "agentic-saa",
            },
            timeout=OPENROUTER_TIMEOUT_S,
        )

    def _openrouter(self, output_format, model, system, messages, effort, max_tokens):
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system}, *messages],
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": output_format.__name__,
                    "strict": True,
                    "schema": _strict_schema(output_format),
                },
            },
            # Route only to a provider that honours response_format, and repair near-JSON.
            "provider": {"require_parameters": True},
            "plugins": [{"id": "response-healing"}],
            "reasoning": {"effort": effort},
            "usage": {"include": True},
        }
        for attempt in range(OPENROUTER_RATE_RETRIES + 1):
            self._pacer.wait()
            response = self._post(payload)
            status = getattr(response, "status_code", 200)
            if status == 200:
                break
            body = _body(response)
            message = str((body.get("error") or {}).get("message") or body or status)
            if status == 429 and "per-day" in message.lower():
                raise QuotaExhausted(
                    f"OpenRouter's daily free-model quota is used up ({message}). It allows 50 "
                    "requests a day, or 1,000 once $10 of credit has been bought."
                )
            if status in (429, 500, 502, 503, 504) and attempt < OPENROUTER_RATE_RETRIES:
                delay = _retry_after(response) or min(60.0, 2.0 ** (attempt + 1))
                log.warning("OpenRouter %s on %s; retrying in %.0fs", status, model, delay)
                self._sleep(delay)
                continue
            raise RuntimeError(f"OpenRouter returned {status} for {model}: {message}")

        body = _body(response)
        if "error" in body:
            raise RuntimeError(f"OpenRouter error for {model}: {body['error']}")
        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        text = message.get("content") or ""
        usage = body.get("usage") or {}
        cost = usage.get("cost")
        if cost is None and model.endswith(":free"):
            cost = 0.0
        refusal = message.get("refusal") or (
            "content filter" if choice.get("finish_reason") == "content_filter" else None
        )
        parsed, error = _parse_json(text)
        if parsed is None and choice.get("finish_reason") == "length":
            error = "response was cut off at max_tokens before the JSON closed"
        details = usage.get("prompt_tokens_details") or {}
        return _Completion(
            parsed=parsed,
            text=text,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            cache_read_tokens=int(details.get("cached_tokens") or 0),
            cost_usd=float(cost) if cost is not None else None,
            refusal=refusal,
            parse_error=error,
        )


def _body(response) -> dict[str, Any]:
    try:
        data = response.json()
    except Exception:
        return {"error": {"message": getattr(response, "text", "")}}
    return data if isinstance(data, dict) else {}


def _retry_after(response) -> float | None:
    headers = getattr(response, "headers", None) or {}
    value = headers.get("Retry-After") or headers.get("retry-after")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _as_text(parsed: Any) -> str:
    if hasattr(parsed, "model_dump_json"):
        return parsed.model_dump_json()
    return json.dumps(parsed, default=str)
