"""The flip-rate pilot: run the anchor over the released 29-item set and report.

Records stream to JSONL as they are made, and a rerun skips whatever is already
there, because upstream's own runner loses a partial run and this one takes hours.

The item set is upstream's and is not vendored here, since that repo still has no
LICENSE file. Fetch it into `data/` first:

    gh api "repos/Abelo9996/llm-judge-consistency/contents/data/eval_pairs.json?ref=067ef9e" \
      --jq .content | base64 -d > data/eval_pairs.json
"""

import argparse
import json
import sys
import time
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path

from src.evaluators.judges import JudgmentRecord
from src.metrics.consistency import flip_rate, position_bias_index
from src.runners.harness import HarnessConfig, Item, run


def load_items(path: Path) -> list[Item]:
    """Upstream's `eval_pairs.json`, whose responses are objects rather than strings."""
    pairs = json.loads(path.read_text())
    return [
        Item(
            id=pair["id"],
            question=pair["question"],
            response_a=pair["response_a"]["text"],
            response_b=pair["response_b"]["text"],
        )
        for pair in pairs
    ]


def load_done(path: Path) -> set[tuple[str, str, str, int]]:
    """The keys already on disk, so a resumed run repeats nothing."""
    if not path.exists():
        return set()
    done = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        done.add((r["protocol"], r["item"], r["position_order"], r["run_index"]))
    return done


def phase(
    items: list[Item],
    config: HarnessConfig,
    out: Path,
    done: set[tuple[str, str, str, int]],
) -> Iterator[str]:
    """Run one protocol item by item, appending each item's records before the next."""
    for index, item in enumerate(items, start=1):
        missing = [
            i
            for i in range(config.replicates)
            for order in config.position_orders
            if (config.protocol, item.id, order, i) not in done
        ]
        if not missing:
            yield f"{config.protocol} {item.id} already done"
            continue

        started = time.perf_counter()
        summary = run([item], config)
        with out.open("a") as handle:
            for record in summary.records:
                handle.write(json.dumps(asdict(record)) + "\n")
        elapsed = time.perf_counter() - started
        yield (
            f"{config.protocol} {index}/{len(items)} {item.id} "
            f"{summary.total} judgments in {elapsed:.0f}s "
            f"({elapsed / max(summary.total, 1):.1f}s each, {summary.unparsed} unparsed)"
        )


def report(records: list[dict]) -> dict:
    """Flip rate and position bias over a finished record log."""
    by_protocol: dict[str, list[dict]] = {}
    for record in records:
        by_protocol.setdefault(record["protocol"], []).append(record)

    out: dict = {}
    for protocol, rows in sorted(by_protocol.items()):
        items = sorted({r["item"] for r in rows})
        rates = []
        biases = []
        for item in items:
            item_rows = [r for r in rows if r["item"] == item]
            ab = [r["winner"] for r in sorted(item_rows, key=_key) if r["position_order"] == "AB"]
            ba = [r["winner"] for r in sorted(item_rows, key=_key) if r["position_order"] == "BA"]
            rate = flip_rate(ab)
            if rate:
                rates.append((item, rate))
            if ba:
                biases.append((item, position_bias_index(ab, ba)))

        total = len(rows)
        unparsed = sum(1 for r in rows if r["unparsed"])
        errors = sum(1 for r in rows if r["error"])
        latencies = [r["latency_ms"] for r in rows if not r["error"]]
        tokens = [r["tokens"] for r in rows if not r["error"]]
        out[protocol] = {
            "judgments": total,
            "items": len(items),
            "unparsed_rate": unparsed / total if total else None,
            "error_count": errors,
            "mean_latency_s": sum(latencies) / len(latencies) / 1000 if latencies else None,
            "mean_tokens": sum(tokens) / len(tokens) if tokens else None,
            "mean_flip_rate": _mean([r.flip_rate for _, r in rates]),
            "max_flip_rate": max((r.flip_rate for _, r in rates), default=None),
            "worst_items": [i for i, _ in sorted(rates, key=lambda p: -p[1].flip_rate)[:3]],
            "position_bias_rate": _mean(
                [b.position_bias_rate for _, b in biases if b.position_bias_rate is not None]
            ),
            "consistent_rate": _mean(
                [b.consistent_rate for _, b in biases if b.consistent_rate is not None]
            ),
        }
    return out


def _key(record: dict) -> int:
    return record["run_index"]


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3-8b")
    parser.add_argument("--items", type=Path, default=Path("data/eval_pairs.json"))
    parser.add_argument("--out", type=Path, default=Path("results/pilot.jsonl"))
    parser.add_argument("--limit", type=int, default=0, help="first N items only")
    parser.add_argument("--flip-repeats", type=int, default=50)
    parser.add_argument("--bias-repeats", type=int, default=30)
    parser.add_argument(
        "--phases",
        default="flip-rate,flip-rate-t0,bias",
        help="comma-separated subset of flip-rate,flip-rate-t0,bias",
    )
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)

    if not args.report_only:
        items = load_items(args.items)
        if args.limit:
            items = items[: args.limit]
        done = load_done(args.out)
        configs = {
            "flip-rate": HarnessConfig(
                model=args.model,
                protocol="flip-rate",
                replicates=args.flip_repeats,
                position_orders=("AB",),
                temperature=1.0,
            ),
            "flip-rate-t0": HarnessConfig(
                model=args.model,
                protocol="flip-rate-t0",
                replicates=args.flip_repeats,
                position_orders=("AB",),
                temperature=0.0,
            ),
            "bias": HarnessConfig(
                model=args.model,
                protocol="bias",
                replicates=args.bias_repeats,
                position_orders=("AB", "BA"),
                temperature=1.0,
            ),
        }
        for name in args.phases.split(","):
            for line in phase(items, configs[name.strip()], args.out, done):
                print(line, flush=True)

    records = [json.loads(l) for l in args.out.read_text().splitlines() if l.strip()]
    json.dump(report(records), sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
