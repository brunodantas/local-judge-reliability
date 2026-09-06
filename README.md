# local-judge-reliability

Which locally served open-weight LLM judge can a small team trust?

This project replicates two 2026 judge-reliability studies on a population
neither covered: open-weight 4-14B judges served locally via llama.cpp, at the
quantizations people actually run on consumer hardware.

- Core: the protocol of "Reliability without Validity" (arXiv 2606.19544),
  unchanged — Cohen's kappa and Krippendorff's alpha, paired AB/BA position
  swaps, temperature-0 replicates — on judges it never ran.
- Arms: quantization, pt-BR judging, temporal stability of frozen local weights
  against hosted-endpoint drift, a hosted-judge comparator, and a rerun of
  "The Coin Flip Judge?" (arXiv 2606.13685) through its released harness.

Both papers name parts of this gap as future work or limitations.

## Status

The harness fork (#2) runs against any OpenAI-compatible endpoint and writes
judgment records. The flip-rate pilot (#12) has run: Qwen3-8B at Q8_0 flips 12.6%
of its verdicts at temperature 1, against 13.3% for GPT-4o-mini in 2606.13685, so
the finding survives being moved onto a quantized local judge. Numbers and cost
are on that issue. The founding spec is #1; the judge matrix is #6.

## Layout

- `CONTEXT.md` — the project glossary
- `docs/architecture.md` — ranked architectural characteristics
- Harness and analysis code land under `src/` as tickets are built

Runs execute on a single consumer GPU (Radeon RX 7800 XT, 15 GB usable);
authoring and CI live here.

## License

MIT.
