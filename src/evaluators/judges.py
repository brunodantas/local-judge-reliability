"""Judge call and verdict parsing, forked from Abelo9996/llm-judge-consistency @067ef9e.

The prompt text and the verdict parser are frozen against upstream; everything
else about the fork is a documented controlled difference.
"""

from dataclasses import dataclass


# Upstream's pairwise template, to be reproduced byte for byte.
PAIRWISE_PROMPT: str = ""


@dataclass(frozen=True)
class JudgmentRecord:
    """One stored judgment, keyed as CONTEXT.md defines a judgment record."""

    judge: str
    benchmark: str
    protocol: str
    item: str
    run_index: int
    position_order: str
    winner: str | None = None
    score: float | None = None
    unparsed: bool = False
    content: str = ""
    tokens: int = 0
    latency_ms: float = 0.0
    error: str | None = None
