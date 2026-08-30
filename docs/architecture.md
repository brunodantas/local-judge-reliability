# Architectural characteristics

Ranked for the harness module, proposed in the founding spec and open to
revision when the first harness ticket runs `/sdlc:ilities`:

1. **Reproducibility** — a reviewer with the repo and a served model gets the
   same judgment records; seeds, configs, and templates are pinned artifacts.
2. **Simplicity** — one runner, two seams (an OpenAI-compatible endpoint in,
   judgment records out); no framework the paper doesn't need.
3. **Portability** — nothing assumes this GPU or ROCm; any OpenAI-compatible
   endpoint works, so anyone's card or a hosted API can re-run the study.

Analysis notebooks are exempt from these; they are single-use science code.
