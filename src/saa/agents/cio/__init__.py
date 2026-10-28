"""CIO agent: the recommended allocation from the compliant ensembles, and the board memo."""

from saa.agents.cio.agent import (
    AGENT,
    CioResult,
    build_prompt,
    candidate_digest,
    decision_body,
    dissent,
    fallback_judgment,
    ips_limits,
    judgment_model,
    load_candidates,
    render_ensembles,
    render_memo,
    render_summary,
    run_cio,
    score_ensembles,
    system_prompt,
)

__all__ = [
    "AGENT",
    "CioResult",
    "build_prompt",
    "candidate_digest",
    "decision_body",
    "dissent",
    "fallback_judgment",
    "ips_limits",
    "judgment_model",
    "load_candidates",
    "render_ensembles",
    "render_memo",
    "render_summary",
    "run_cio",
    "score_ensembles",
    "system_prompt",
]
