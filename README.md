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

Spec stage. The founding spec is issue #1; no harness code yet.

## Layout

- `CONTEXT.md` — the project glossary
- `docs/architecture.md` — ranked architectural characteristics
- Harness and analysis code land under `src/` as tickets are built

Runs execute on a single consumer GPU (Radeon RX 7800 XT, 15 GB usable);
authoring and CI live here.

## License

MIT.
