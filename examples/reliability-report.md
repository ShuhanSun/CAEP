# CAEP Reliability Report

## Summary

- Runs: 5
- Successful runs: 3
- Success rate: 60.0%
- Cost coverage: 100.0%
- Cost per success: $6.36
- Mixed-outcome task fraction: 100.0%

## Task stability

| Task | Runs | Successes | Success rate | Outcome class | Entropy (bits) | Cost CV | Latency CV |
|---|---:|---:|---:|---|---:|---:|---:|
| demo/reliability-task | 5 | 3 | 60.0% | mixed_outcome | 0.971 | 0.345 | 0.014 |

## Interpretation

`mixed_outcome` means the same task succeeded in some clean repetitions and failed in others. CAEP reports this directly instead of collapsing it into a single pass/fail label.

Outcome entropy is 0 bits for perfectly consistent outcomes and approaches 1 bit when success/failure is maximally mixed. It is descriptive, not a composite quality score.

