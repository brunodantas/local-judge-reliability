"""The frozen oracle for the harness fork, one test per case in
docs/specs/02-harness-fork.md.

Every case reads the judgment-record log or the request the stub received; the
inter-call delay is the one exception, and it is observed through an injected sleep.
"""

from src.runners.harness import HarnessConfig, Item, run

JUDGE = "qwen3-8b"

# Copied from PAIRWISE_PROMPT in src/evaluators/judges.py of
# Abelo9996/llm-judge-consistency @067ef9e. The oracle holds its own copy so that
# case 2 binds against upstream rather than against the fork's own constant.
UPSTREAM_PAIRWISE_PROMPT = """You are an impartial judge. Compare the two responses below to the given question and decide which is better.

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


def config(**overrides) -> HarnessConfig:
    """One item, one order, one replicate, unless the case says otherwise."""
    settings = {"model": JUDGE, "replicates": 1, "position_orders": ("AB",)}
    settings.update(overrides)
    return HarnessConfig(**settings)


def by_run_index(records):
    return sorted(records, key=lambda r: r.run_index)


# --- Endpoint seam ---------------------------------------------------------


def test_requests_reach_the_configured_endpoint(stub, item):
    stub.always_verdict("The verdict is [[A]]")

    summary = run([item], config())

    assert len(stub.requests) == 1
    assert stub.requests[0]["path"].endswith("/chat/completions")
    assert len(summary.records) == 1
    assert summary.records[0].judge == JUDGE


def test_the_pairwise_prompt_is_byte_identical_to_upstream(stub, item):
    stub.always_verdict("[[A]]")

    run([item], config())

    messages = stub.bodies[0]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == UPSTREAM_PAIRWISE_PROMPT.format(
        question=item.question,
        response_a=item.response_a,
        response_b=item.response_b,
    )


# --- Verdict parsing, frozen as upstream wrote it --------------------------


def test_a_bracketed_a_is_a_win_for_a(stub, item):
    stub.always_verdict("Response A reasons better. [[A]]")

    record = run([item], config()).records[0]

    assert record.winner == "A"
    assert record.score == 1
    assert record.unparsed is False


def test_a_bracketed_b_is_a_win_for_b(stub, item):
    stub.always_verdict("Response B reasons better. [[B]]")

    record = run([item], config()).records[0]

    assert record.winner == "B"
    assert record.score == -1
    assert record.unparsed is False


def test_a_bracketed_tie_is_a_tie(stub, item):
    stub.always_verdict("Neither is better. [[tie]]")

    record = run([item], config()).records[0]

    assert record.winner == "tie"
    assert record.score == 0
    assert record.unparsed is False


def test_an_untagged_verdict_is_stored_as_unparsed(stub, item):
    stub.always_verdict("Response A is clearly better.")

    summary = run([item], config())
    record = summary.records[0]

    assert record.unparsed is True
    assert record.winner is None
    assert record.content == "Response A is clearly better."
    assert summary.unparsed == 1


def test_a_lowercase_bracketed_a_is_unparsed_not_a_win_for_a(stub, item):
    stub.always_verdict("[[a]]")

    record = run([item], config()).records[0]

    assert record.unparsed is True
    assert record.winner is None


def test_a_verdict_holding_both_tags_resolves_to_a(stub, item):
    stub.always_verdict("Arguably [[B]], but on balance [[A]].")

    record = run([item], config()).records[0]

    assert record.winner == "A"


# --- Endpoint failure ------------------------------------------------------


def test_an_endpoint_error_is_recorded_and_the_run_continues(stub, item):
    stub.queue_verdict("[[A]]")
    stub.queue_error(500)
    stub.queue_verdict("[[B]]")

    records = by_run_index(run([item], config(replicates=3)).records)

    assert len(records) == 3
    assert records[0].winner == "A"
    assert records[2].winner == "B"
    assert records[1].winner is None
    assert records[1].error
    assert "500" in records[1].error
    assert records[1].latency_ms > 0


# --- Position order --------------------------------------------------------


def test_ab_and_ba_are_two_records_on_one_item_told_apart_by_a_field(stub, item):
    stub.always_verdict("[[A]]")

    records = run([item], config(position_orders=("AB", "BA"))).records

    assert len(records) == 2
    assert [r.item for r in records] == ["q001", "q001"]
    assert {r.position_order for r in records} == {"AB", "BA"}


def test_the_ba_request_presents_the_responses_swapped(stub, item):
    stub.always_verdict("[[A]]")

    run([item], config(position_orders=("BA",)))

    assert stub.bodies[0]["messages"][0]["content"] == UPSTREAM_PAIRWISE_PROMPT.format(
        question=item.question,
        response_a=item.response_b,
        response_b=item.response_a,
    )


# --- Replicates ------------------------------------------------------------


def test_n_replicates_give_n_records_numbered_zero_upward(stub, item):
    stub.always_verdict("[[A]]")

    records = run([item], config(replicates=5)).records

    assert len(records) == 5
    assert sorted(r.run_index for r in records) == [0, 1, 2, 3, 4]


# --- Configuration ---------------------------------------------------------


def test_temperature_defaults_to_upstream_and_the_configured_value_reaches_the_request(
    stub, item
):
    stub.always_verdict("[[A]]")

    run([item], config())
    run([item], config(temperature=0.0))

    assert stub.bodies[0]["temperature"] == 1.0
    assert stub.bodies[1]["temperature"] == 0.0


def test_the_delay_defaults_to_upstream_and_a_configured_zero_removes_it(stub, item):
    stub.always_verdict("[[A]]")
    default_sleeps: list[float] = []
    zero_sleeps: list[float] = []

    run([item], config(replicates=2), sleep=default_sleeps.append)
    run([item], config(replicates=2, delay_seconds=0), sleep=zero_sleeps.append)

    assert default_sleeps
    assert all(seconds == 0.3 for seconds in default_sleeps)
    assert all(seconds == 0 for seconds in zero_sleeps)


def test_reasoning_suppression_is_sent_with_the_request(stub, item):
    stub.always_verdict("[[A]]")

    run([item], config(suppress_reasoning=True))

    body = stub.bodies[0]
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["messages"][0]["content"] == UPSTREAM_PAIRWISE_PROMPT.format(
        question=item.question,
        response_a=item.response_a,
        response_b=item.response_b,
    )


def test_the_token_cap_is_configuration_defaulting_to_upstream(stub, item):
    stub.always_verdict("[[A]]")

    run([item], config())
    run([item], config(max_tokens=2048))

    assert stub.bodies[0]["max_tokens"] == 512
    assert stub.bodies[1]["max_tokens"] == 2048


# --- Record contents -------------------------------------------------------


def test_every_record_carries_the_full_key(stub, item):
    stub.always_verdict("[[A]]")

    record = run([item], config()).records[0]

    assert record.judge == JUDGE
    assert record.benchmark == "13685-29"
    assert record.protocol == "flip-rate"
    assert record.item == "q001"
    assert record.run_index == 0
    assert record.position_order == "AB"


def test_every_record_carries_its_own_wall_clock_and_token_count(stub, item):
    stub.always_verdict("[[A]]", total_tokens=18)

    record = run([item], config()).records[0]

    assert record.latency_ms > 0
    assert record.tokens == 18


def test_a_response_with_no_usage_block_records_zero_tokens(stub, item):
    stub.always_verdict("[[A]]", with_usage=False)

    record = run([item], config()).records[0]

    assert record.tokens == 0
    assert record.winner == "A"
    assert record.unparsed is False


# --- Run summary -----------------------------------------------------------


def test_the_run_reports_how_many_verdicts_went_unparsed(stub, item):
    untagged = "Response A is clearly better."
    for index in range(10):
        stub.queue_verdict(untagged if index in (1, 4, 8) else "[[A]]")

    summary = run([item], config(replicates=10))

    assert summary.total == 10
    assert summary.unparsed == 3
