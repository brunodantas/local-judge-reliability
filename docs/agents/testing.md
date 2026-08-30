# Testing

## Runner

`uv` manages the environment; `pytest` runs the tests. Python 3.14, pinned in
`.python-version`.

Inner loop, one file at a time:

```
uv run pytest tests/test_harness.py
```

Whole suite:

```
uv run pytest
```

`pythonpath = ["."]` in `pyproject.toml` puts the repo root on `sys.path`, so
`src.evaluators.judges` imports the way it does upstream without an install step.

## No live models in tests

Harness tests run against the stub OpenAI-compatible endpoint in
`tests/conftest.py`, a stdlib HTTP server on a loopback port with
`OPENAI_BASE_URL` pointed at it. That path exercises the same environment
variable a real run uses, so a regression in the endpoint seam fails here rather
than on the box.

## Frozen oracles

A ticket's tests are written before its code and committed as a freeze. Find one
with `git log --grep="freeze oracle for"`. Changing what a frozen test asserts is
a decision for the repo owner, not for the implementing session.
