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
