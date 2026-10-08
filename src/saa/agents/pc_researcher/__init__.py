"""PC-researcher agent: proposes a portfolio-construction method the registry lacks (§3.4)."""

from saa.agents.pc_researcher.agent import (
    AGENT,
    AGENT_ID,
    DEFAULT_METHOD,
    ResearchChoice,
    ResearchOutcome,
    build_prompt,
    library_options,
    research,
)

__all__ = [
    "AGENT",
    "AGENT_ID",
    "DEFAULT_METHOD",
    "ResearchChoice",
    "ResearchOutcome",
    "build_prompt",
    "library_options",
    "research",
]
