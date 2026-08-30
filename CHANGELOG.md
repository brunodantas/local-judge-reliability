# Changelog

All notable changes to this project. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[SemVer](https://semver.org/).

## [Unreleased]

### Added

- Repo scaffold: README, glossary (`CONTEXT.md`), ranked architectural
  characteristics, MIT license.
- Cases for the harness fork (`docs/specs/02-harness-fork.md`), 20 of them,
  plus the five open questions they settled.
- Glossary terms for the judgment record's new keys: benchmark, protocol,
  position order.
- Frozen oracle for the harness fork: 20 tests over a stub OpenAI-compatible
  endpoint, with the stub interface they import (`src/evaluators/judges.py`,
  `src/runners/harness.py`). No implementation yet.
- Python tooling: `uv` and `pytest` on Python 3.14, with the runner recorded in
  `docs/agents/testing.md`.
- The harness fork itself: `judge_pairwise` and the verdict parser in
  `src/evaluators/judges.py`, the run loop in `src/runners/harness.py`. It reaches
  an OpenAI-compatible endpoint through `OPENAI_BASE_URL` and writes one judgment
  record per call. All 20 frozen tests pass, and one manual run against the box's
  llama-server judged an item in both position orders.
- Five controlled differences from upstream (`Abelo9996/llm-judge-consistency`
  @067ef9e), each recorded rather than silently edited:
  - Temperature, the inter-call delay, and `max_tokens` are configuration, keeping
    upstream's 1.0, 0.3s, and 512 as defaults. Upstream hardcodes all three inside
    `judge_pairwise`, and the delay alone is 43 minutes across an 8,700-call run.
  - A judgment record gains `benchmark`, `protocol`, and `position_order`. Upstream
    tells AB from BA by a suffix on `sample_id` (`q001_orig`, `q001_swap`).
  - An unrecognised verdict is flagged and counted, where upstream gives it
    `score=0` and makes it indistinguishable from a tie.
  - The request carries `chat_template_kwargs: {"enable_thinking": false}`, which
    upstream cannot express. A reasoning judge spends the 512-token cap before it
    emits its verdict tag.
  - The SDK client sets `max_retries=0`, so one endpoint failure is one judgment
    record. Upstream's bare `OpenAI()` retries twice and hides the first two.
  The prompt template and the verdict parser are byte-identical to upstream,
  checked against the GitHub API at that commit.
