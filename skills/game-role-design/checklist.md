# Design: review checklist (verdicts only)

Mark each line passed, a note, or `not-assessed` with the reason. Notes are `advisory` unless a check written into the frozen acceptance fails by measurement. An anchor (a label, a chosen reference or a page rule) decides whether a note can fail a verdict item through its `item`, never its severity. Read the `review` items that name `design` first. Never run on a feature.

## Checked first (from bot traces and metrics)

- Completability: the share of seeded runs that reach the end, against the page's number.
- Difficulty curve: deaths or damage per beat, against the beat chart.
- Decisions per minute: the median, and the longest stretch with none.
- Source/sink balance: each resource's net per minute, and any that only grows or only drains.

## Judged (from the traces)

- Dominant strategy: one option chosen in nearly all runs, or one build that wins every run. Quote the trace.
- Boring stretch: a span with no decision or no change of pressure. Name the span.
- Role clarity: each piece of content has a role and a counter on the Content page, and the trace shows both used.
- Run variance: two runs from different seeds differ in what the player decided, not only in numbers.

## Needs the person

- Whether it's fun to replay: never a note; `not-assessed` until the person plays.
- Taste about difficulty: `not-assessed` without labels.
