# Harness fork onto the local endpoint

The contract for ticket #2, under the founding spec in issue #1. Upstream is
`Abelo9996/llm-judge-consistency` at `067ef9e`, read on 2026-08-30.

The unit is the fork alone. It emits judgment records against a stub
OpenAI-compatible endpoint. No metrics, no resume, no measured run.

## Decisions settled while deriving the cases

Five questions the ticket left open, answered 2026-08-30 before any test was written.

**The delay is observed through an injected sleep.** Every other case reads the
judgment-record log, per the testing decisions in issue #1. The inter-call delay is the
one thing the log cannot show, and asserting on wall-clock is a race. The runner takes a
sleep function, and the test asserts the configured value reached it.

**Reasoning suppression travels in the request, not the prompt.** The harness sends
`chat_template_kwargs: {"enable_thinking": false}`, which llama-server honours for Qwen 3.
Putting suppression in prompt text would break case 2, which freezes the prompt byte for
byte against upstream.

**This ticket writes records and computes nothing.** Flip rate and position bias are
read off the log in #12 using upstream's `consistency.py` untouched. Keeping the metric
code outside the frozen oracle leaves it free for the kappa and alpha work in #3 and #4.

**`max_tokens` is configuration, defaulting to upstream's 512.** Reasoning suppression
is already a controlled difference, so the cap that interacts with it moves with it.

**`benchmark` and `protocol` take fixed vocabulary.** For this ticket, `benchmark` is
`13685-29` and `protocol` is `flip-rate`. Both terms are in `CONTEXT.md` so later tickets
inherit the naming rather than inventing their own.

## Cases

### Endpoint seam

1. **Requests reach the configured endpoint**
   - Given: `OPENAI_BASE_URL` points at the stub endpoint
   - When: the harness runs one pairwise judgment on one item
   - Then: the stub receives exactly one chat-completions request, and one judgment
     record is written naming the configured model

2. **The pairwise prompt is byte-identical to upstream**
   - Given: an item with a known question and two known responses
   - When: the harness requests one pairwise judgment on it
   - Then: the request carries a single user message equal to upstream's
     `PAIRWISE_PROMPT` formatted with that item's three fields, character for
     character, and carries no system message

### Verdict parsing, frozen as upstream wrote it

3. **A bracketed A is a win for A**
   - Given: the stub returns a verdict containing `[[A]]`
   - When: the harness parses it
   - Then: the record has winner `A`, score 1, and is not marked unparsed

4. **A bracketed B is a win for B**
   - Given: the stub returns a verdict containing `[[B]]`
   - When: the harness parses it
   - Then: the record has winner `B`, score -1, and is not marked unparsed

5. **A bracketed tie is a tie**
   - Given: the stub returns a verdict containing `[[tie]]`
   - When: the harness parses it
   - Then: the record has winner `tie`, score 0, and is not marked unparsed

6. **An untagged verdict is stored as unparsed**
   - Given: the stub returns `Response A is clearly better.` with no bracketed tag
   - When: the harness parses it
   - Then: the record is marked unparsed, has no winner, keeps the raw content, and
     increments the run's unparsed count. An unparsed verdict is distinguishable from
     a tie, which upstream's bare `score=0` is not.

7. **A lowercase bracketed a is unparsed, not a win for A**
   - Given: the stub returns a verdict containing `[[a]]` and nothing else recognisable
   - When: the harness parses it
   - Then: the record is marked unparsed and has no winner

   Upstream matches `[[A]]` case-sensitively and lowercases the content only for the
   tie check. The quirk is frozen deliberately; case 6's counter is what stops it being
   silent on a local judge.

8. **A verdict holding both tags resolves to A**
   - Given: the stub returns content containing both `[[A]]` and `[[B]]`
   - When: the harness parses it
   - Then: the record has winner `A`

   This is upstream's if/elif order, frozen.

### Endpoint failure

9. **An endpoint error is recorded and the run continues**
   - Given: the stub returns HTTP 500 on the second of three requests
   - When: the harness runs three replicates on one item
   - Then: three records exist; the second carries the error text, no winner, and a
     latency; the first and third carry parsed verdicts

### Position order

10. **AB and BA are two records on one item, told apart by a field**
    - Given: an item with id `q001`
    - When: the harness judges it in both position orders
    - Then: two records exist, both with item `q001`, one with position order `AB` and
      one with `BA`, and neither carries a suffix on the item id

11. **The BA request presents the responses swapped**
    - Given: an item whose responses are known
    - When: the harness requests the BA judgment
    - Then: the request's Response A block holds the item's `response_b` text and its
      Response B block holds the item's `response_a` text

### Replicates

12. **N replicates give N records numbered zero upward**
    - Given: replicates configured to 5
    - When: the harness runs one item in one position order
    - Then: five records exist for that item and order, with run indexes 0 through 4,
      no gaps and no repeats

### Configuration

13. **Temperature defaults to upstream's value and the configured value reaches the request**
    - Given: no temperature configured, then temperature configured to 0.0
    - When: the harness requests a judgment under each
    - Then: the first request carries temperature 1.0 and the second carries 0.0

14. **The delay defaults to upstream's value and a configured zero removes it**
    - Given: an injected sleep function, and the delay left unset, then set to 0
    - When: the harness runs two judgments under each
    - Then: the first run calls sleep with 0.3, and the second calls it with 0 or not
      at all

15. **Reasoning suppression is sent with the request**
    - Given: suppression enabled
    - When: the harness requests a judgment
    - Then: the request body carries `chat_template_kwargs` with `enable_thinking`
      false, and the prompt text is unchanged from case 2

16. **The token cap is configuration, defaulting to upstream's**
    - Given: no cap configured, then a cap of 2048
    - When: the harness requests a judgment under each
    - Then: the first request carries `max_tokens` 512 and the second carries 2048

### Record contents

17. **Every record carries the full key**
    - Given: any completed judgment
    - When: its record is read from the log
    - Then: judge, benchmark, protocol, item, run index, and position order are all
      present and non-empty, with benchmark `13685-29` and protocol `flip-rate`

18. **Every record carries its own wall-clock and token count**
    - Given: a stub that reports a known token usage
    - When: one judgment completes
    - Then: the record's latency is greater than zero and its token count equals the
      usage the stub reported

19. **A response with no usage block records zero tokens**
    - Given: a stub response omitting the usage object
    - When: one judgment completes
    - Then: the record's token count is zero and the judgment is otherwise intact

    Upstream falls back to zero rather than failing; frozen.

### Run summary

20. **The run reports how many verdicts went unparsed**
    - Given: a run of 10 judgments in which the stub returns an untagged verdict 3 times
    - When: the run finishes
    - Then: the run summary reports 3 unparsed of 10
