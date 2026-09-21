# Task Stability Profile — draft

Repeated coding-agent runs should not be collapsed into a single pass/fail label when the same task exhibits both outcomes.

CAEP reports three threshold-free outcome classes:

- `consistent_success`: every observed clean repetition succeeds.
- `consistent_failure`: every observed clean repetition fails.
- `mixed_outcome`: at least one repetition succeeds and at least one fails.

It also reports Bernoulli outcome entropy in bits:

`H(p) = -p log2(p) - (1-p) log2(1-p)`

where `p` is the observed success fraction. Entropy is 0 for perfectly consistent outcomes and reaches 1 bit at a 50/50 split. This is a descriptive instability statistic, not a quality score.

For cost and latency, CAEP may report coefficient of variation when at least two measurements are known and the mean is non-zero. Unknown measurements must remain unknown rather than being imputed as zero.

The protocol intentionally does not call 4/5 successes "stable". Any such threshold would be an analysis policy layered on top of the raw profile, not part of the base evidence standard.
