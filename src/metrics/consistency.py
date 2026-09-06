"""Flip rate and position bias, frozen against upstream's `src/metrics/consistency.py`.

Reimplemented rather than imported, because upstream has no LICENSE file; the
definitions are kept identical so the numbers stay comparable to the paper's.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class FlipRate:
    """How often one item's winner departs from its own majority."""

    flip_rate: float
    majority_winner: str
    majority_rate: float
    distribution: dict[str, int]
    n: int


@dataclass(frozen=True)
class PositionBias:
    """Paired AB/BA outcomes for one item."""

    consistent_rate: float | None
    position_bias_rate: float | None
    n: int


def flip_rate(winners: Sequence[str | None]) -> FlipRate | None:
    """Upstream's definition: the share of valid verdicts that differ from the majority."""
    valid = [w for w in winners if w is not None]
    if len(valid) < 2:
        return None

    counts = Counter(valid)
    winner, count = counts.most_common(1)[0]
    flips = sum(1 for w in valid if w != winner)
    return FlipRate(
        flip_rate=flips / len(valid),
        majority_winner=winner,
        majority_rate=count / len(valid),
        distribution=dict(counts),
        n=len(valid),
    )


def position_bias_index(
    original: Sequence[str | None], swapped: Sequence[str | None]
) -> PositionBias:
    """Upstream's definition, over verdicts paired by run index.

    A judgment is consistent when the verdict tracks the swap, and position-biased when
    the same letter wins both ways; a tie on one side only is neither.
    """
    pairs = [(o, s) for o, s in zip(original, swapped) if o is not None and s is not None]
    consistent = sum(
        1
        for o, s in pairs
        if (o == "A" and s == "B") or (o == "B" and s == "A") or (o == "tie" and s == "tie")
    )
    biased = sum(1 for o, s in pairs if o == s and o != "tie")
    n = len(pairs)
    return PositionBias(
        consistent_rate=consistent / n if n else None,
        position_bias_rate=biased / n if n else None,
        n=n,
    )
