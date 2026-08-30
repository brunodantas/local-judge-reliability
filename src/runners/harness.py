"""The pairwise judging run: items in, judgment records out.

The endpoint is whatever OPENAI_BASE_URL names, so there is no URL parameter here.
"""

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from src.evaluators.judges import JudgmentRecord


@dataclass(frozen=True)
class Item:
    """One prompt with its fixed pair of candidate responses."""

    id: str
    question: str
    response_a: str
    response_b: str


@dataclass(frozen=True)
class HarnessConfig:
    """Everything upstream hardcoded, plus the record keys upstream lacked."""

    model: str
    benchmark: str = "13685-29"
    protocol: str = "flip-rate"
    replicates: int = 1
    position_orders: Sequence[str] = ("AB", "BA")
    temperature: float = 1.0
    delay_seconds: float = 0.3
    max_tokens: int = 512
    suppress_reasoning: bool = True


@dataclass(frozen=True)
class RunSummary:
    """The record log for one run, with the counts read off it."""

    records: list[JudgmentRecord] = field(default_factory=list)
    total: int = 0
    unparsed: int = 0


def run(
    items: Sequence[Item],
    config: HarnessConfig,
    sleep: Callable[[float], None] = time.sleep,
) -> RunSummary:
    """Judge every item in every configured position order, `replicates` times each.

    The sleep is injected because the inter-call delay is the one behaviour the
    record log cannot show.
    """
    raise NotImplementedError
