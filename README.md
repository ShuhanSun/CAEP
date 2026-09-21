# CAEP — Coding Agent Evaluation Protocol

CAEP is a **benchmark-neutral reliability and evidence layer** for coding-agent evaluation.

It does **not** replace Harbor, SWE-bench, Terminal-Bench, or ATIF. It consumes their outputs and adds the
pieces required to answer questions such as:

- Is an agent's result reproducible across repeated runs?
- What is the true cost per successful task, including failed attempts?
- Can a public leaderboard result be independently audited?
- Which exact execution stack produced the score?
- Are two reported results actually comparable?

## Why v0.2 changed the design

Harbor already standardizes agent trajectories with **ATIF**. CAEP v0.2 therefore treats
`agent/trajectory.json` (ATIF) as the canonical raw interaction trace instead of inventing another competing
trace schema.

CAEP adds three layers on top:

1. **Run identity/provenance** — exact benchmark, task, agent, model, harness, environment and policy.
2. **Evidence bundles** — content-addressed artifacts and explicit omissions.
3. **Repeated-run reliability** — success rate, observed Pass@k, cost per success, uncertainty, and later
   recovery/regression metrics.

## Prototype CLI

Import an existing Harbor job:

```bash
caep import-harbor ~/.harbor/jobs/my-job --out caep-runs
```

Aggregate imported runs:

```bash
caep aggregate caep-runs --out aggregate.json
```

Verify artifact hashes:

```bash
caep verify caep-runs/<run-id>
```

No API keys are needed to import and analyze completed jobs.

## Task stability profiles

CAEP preserves repeated-run behavior instead of collapsing it into one pass/fail label:

- `consistent_success` — all observed repetitions succeed.
- `consistent_failure` — all observed repetitions fail.
- `mixed_outcome` — the same task succeeds in some clean repetitions and fails in others.

It also reports Bernoulli outcome entropy (0–1 bit), cost coefficient of variation, and latency coefficient of variation when enough measurements are available. These are descriptive statistics, not a composite quality score.

Generate a Markdown report from aggregate output:

```bash
caep report aggregate.json --out reliability-report.md
```

## Metrics in v0.2

For a comparable set of repeated runs:

- `success_rate = successful_runs / total_runs`
- `mean_known_run_cost_usd = sum(cost of known-cost runs) / known_cost_runs`
- `observed_pass_at_k = 1` when at least one of the observed k runs succeeds
- `cost_per_success = sum(cost of ALL runs) / successful_runs`
- Wilson 95% confidence interval for success rate when `n > 0`

**Failed runs remain in the cost numerator.**
When cost coverage is 100%, `mean_known_run_cost_usd` is the nominal per-run cost for repeated-run comparisons.

CAEP deliberately does not emit a single composite "reliability score."

## Recovery metrics

Recovery is important, but generic recovery cannot be inferred reliably from an arbitrary agent trace.
CAEP v0.2 therefore refuses to fabricate it. Recovery annotations are a separate, explicit layer planned for
the next milestone.

## Current status

Research prototype. The next milestone is to run repeated evaluations across at least two agents and two
benchmarks and publish the raw CAEP bundles plus analysis.
