"""Judge call and verdict parsing, forked from Abelo9996/llm-judge-consistency @067ef9e.

The prompt text and the verdict parser are frozen against upstream; everything
else about the fork is a documented controlled difference.
"""

import time
from dataclasses import dataclass

from openai import OpenAI


# Upstream's pairwise template, reproduced byte for byte.
PAIRWISE_PROMPT: str = """You are an impartial judge. Compare the two responses below to the given question and decide which is better.

[Question]
{question}

[Response A]
{response_a}

[Response B]
{response_b}

Evaluate based on helpfulness, relevance, accuracy, depth, and clarity.
First provide a brief explanation, then output your verdict as exactly one of:
[[A]] if Response A is better
[[B]] if Response B is better
[[tie]] if they are equally good"""


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


@dataclass(frozen=True)
class Verdict:
    """The parsed form of one verdict string."""

    winner: str | None
    score: float | None
    unparsed: bool


@dataclass(frozen=True)
class JudgeReply:
    """One round trip to the judge, whether it answered or failed."""

    content: str
    tokens: int
    latency_ms: float
    error: str | None = None


# A call that never returned has no verdict to parse, which is not an unparsed verdict.
NO_VERDICT: Verdict = Verdict(winner=None, score=None, unparsed=False)


def get_client() -> OpenAI:
    """A bare client as upstream, so the SDK reads `OPENAI_BASE_URL` from the environment.

    Retries are off so that one endpoint failure is one judgment record, rather than a
    call the SDK quietly repeats.
    """
    return OpenAI(max_retries=0)


def parse_verdict(content: str) -> Verdict:
    """Upstream's if/elif chain, frozen, so the tags stay case-sensitive and only the
    tie check lowercases.

    Upstream scores an unrecognised verdict zero; this flags it instead, which is what
    tells it apart from a tie.
    """
    if "[[A]]" in content:
        return Verdict(winner="A", score=1, unparsed=False)
    if "[[B]]" in content:
        return Verdict(winner="B", score=-1, unparsed=False)
    if "[[tie]]" in content.lower():
        return Verdict(winner="tie", score=0, unparsed=False)
    return Verdict(winner=None, score=None, unparsed=True)


def judge_pairwise(
    client: OpenAI,
    model: str,
    question: str,
    response_a: str,
    response_b: str,
    *,
    temperature: float,
    max_tokens: int,
    suppress_reasoning: bool,
) -> JudgeReply:
    """Ask the judge once which of the two responses is better.

    Temperature, the token cap, and reasoning suppression are parameters here because
    upstream hardcodes the first two and cannot express the third.
    """
    prompt = PAIRWISE_PROMPT.format(
        question=question, response_a=response_a, response_b=response_b
    )
    extra_body = (
        {"chat_template_kwargs": {"enable_thinking": False}}
        if suppress_reasoning
        else {}
    )

    start = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            extra_body=extra_body,
        )
    except Exception as failure:
        return JudgeReply(
            content="", tokens=0, latency_ms=_elapsed_ms(start), error=str(failure)
        )

    return JudgeReply(
        content=response.choices[0].message.content or "",
        tokens=response.usage.total_tokens if response.usage else 0,
        latency_ms=_elapsed_ms(start),
    )


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000
