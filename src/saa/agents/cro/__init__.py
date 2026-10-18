"""The Chief Risk Officer agent: one standardised risk report per candidate (stage 5)."""

from saa.agents.cro.agent import (
    AGENT,
    MIN_COMMENTARY_CHARS,
    CroResult,
    Report,
    assess,
    body_from,
    build_prompt,
    load_proposals,
    profile_proposal,
    render_summary,
    run_cro,
    system_prompt,
    write_summary,
)

__all__ = [
    "AGENT",
    "MIN_COMMENTARY_CHARS",
    "CroResult",
    "Report",
    "assess",
    "body_from",
    "build_prompt",
    "load_proposals",
    "profile_proposal",
    "render_summary",
    "run_cro",
    "system_prompt",
    "write_summary",
]
