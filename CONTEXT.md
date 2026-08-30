# Judge Reliability

Glossary for the open-weight judge-reliability replication. One term per
concept; the spec, tickets, code, and paper all use these.

## Language

**Judge**:
An LLM asked to pick the better of two responses to the same prompt.
_Avoid_: evaluator, grader, rater

**Judgment**:
One verdict (A, B, or tie) from one judge on one item in one position order.
_Avoid_: evaluation, call, vote

**Judgment record**:
The stored form of one judgment, keyed by judge, benchmark, protocol, item,
run index, and position order.
_Avoid_: result row, log entry

**Item**:
One prompt with its fixed pair of candidate responses.
_Avoid_: question, pair, sample

**Benchmark**:
The named item set a judgment came from. `13685-29` is the 29-item set released with
2606.13685; the English core adds MT-Bench, JudgeBench, and RewardBench.
_Avoid_: dataset, corpus, eval set

**Protocol**:
The named measurement a judgment belongs to: `flip-rate`, `agreement`, `bias`,
`consistency`. Upstream's `eval_format` field conflates this with the question shape
(pairwise or pointwise), which we keep as a separate field.
_Avoid_: experiment, phase, eval format

**Position order**:
Which response the judge saw first, `AB` or `BA`. A field on the judgment record, never
a suffix on the item id.
_Avoid_: orig/swap, direction, arrangement

**Core**:
The exact replication of the 2606.19544 protocol on new judges.
_Avoid_: baseline, main experiment

**Arm**:
A named extension that varies one thing the core holds fixed.
_Avoid_: track, experiment, phase

**Anchor**:
Qwen 3 8B, the one judge shared with 2606.19544's cohort; the bridge between
our numbers and theirs.
_Avoid_: reference judge, overlap model

**Reference quant**:
The quantization at which a judge family gets the full protocol; other quants
get agreement and bias only.
_Avoid_: default quant, base quant

**Replicate**:
One independent repeat of a judgment under identical settings, for
test-retest consistency.
_Avoid_: rerun, trial, repeat

**Flip**:
A judge reversing its verdict on the same item across replicates or position
orders.
_Avoid_: inconsistency, disagreement

**Position bias**:
Systematic preference for the response shown first (or last), measured by
paired AB/BA evaluations.
_Avoid_: order bias, first-position effect

**Controlled difference**:
A deliberate, documented deviation from the replicated paper's setup, with the
reason recorded.
_Avoid_: adaptation, caveat, deviation

**Frontier arm**:
The three hosted judges from 2606.19544's cohort rerun via API, anchoring our
pipeline to published numbers and serving as the drift comparator.
_Avoid_: API arm, cloud arm
