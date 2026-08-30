"""The pairwise judging run: items in, judgment records out.

The endpoint is whatever OPENAI_BASE_URL names, so there is no URL parameter here.
"""

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from src.evaluators.judges import (
    NO_VERDICT,
    JudgeReply,
    JudgmentRecord,
    get_client,
    judge_pairwise,
    parse_verdict,
)


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
    client = get_client()
    records: list[JudgmentRecord] = []

    for item in items:
        for position_order in config.position_orders:
            first, second = _as_shown(item, position_order)
            for run_index in range(config.replicates):
                reply = judge_pairwise(
                    client,
                    config.model,
                    item.question,
                    first,
                    second,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    suppress_reasoning=config.suppress_reasoning,
                )
                records.append(
                    _to_record(config, item, run_index, position_order, reply)
                )
                sleep(config.delay_seconds)

    return RunSummary(
        records=records,
        total=len(records),
        unparsed=sum(1 for record in records if record.unparsed),
    )


def _as_shown(item: Item, position_order: str) -> tuple[str, str]:
    """The pair as the judge sees it, swapped for `BA` so the swap never reaches the
    record's item id."""
    if position_order == "BA":
        return item.response_b, item.response_a
    return item.response_a, item.response_b


def _to_record(
    config: HarnessConfig,
    item: Item,
    run_index: int,
    position_order: str,
    reply: JudgeReply,
) -> JudgmentRecord:
    """Stamp one reply with the six keys a judgment record is filed under."""
    verdict = NO_VERDICT if reply.error else parse_verdict(reply.content)
    return JudgmentRecord(
        judge=config.model,
        benchmark=config.benchmark,
        protocol=config.protocol,
        item=item.id,
        run_index=run_index,
        position_order=position_order,
        winner=verdict.winner,
        score=verdict.score,
        unparsed=verdict.unparsed,
        content=reply.content,
        tokens=reply.tokens,
        latency_ms=reply.latency_ms,
        error=reply.error,
    )
