# First Experiment Plan

## Research question

Does single-run coding-agent evaluation materially overstate or understate practical reliability and economic
efficiency compared with repeated-run evaluation?

## Minimal experiment

- Benchmarks:
  - SWE-bench Verified subset
  - one repository-generation / long-horizon benchmark such as Zero2Repo
- Agents:
  - Codex
  - Claude Code
  - OpenHands
- Repetitions:
  - 5 clean runs per task
- Initial task count:
  - 25 tasks per benchmark for pilot
- Primary metrics:
  - task success rate
  - task-level repeated-run success distribution
  - observed Pass@5
  - total cost
  - cost per successful run
  - wall time
- Secondary:
  - token distribution
  - variance across repeats
  - harness/environment provenance completeness

## Core hypotheses

H1. A non-trivial fraction of tasks exhibit unstable outcomes across five clean repetitions.

H2. Ranking agents by one-shot success can differ from ranking them by cost per success.

H3. Failed attempts contribute enough cost that excluding them materially biases economic comparisons.

## Publication-worthy contribution threshold

Do not publish merely because CAEP exists. The paper needs an empirical finding that changes how coding-agent
evaluation should be interpreted or reported.

A strong result would show that:
- repeated-run instability is substantial and systematic,
- cost-per-success changes conclusions versus nominal per-run cost,
- or execution-stack provenance explains a meaningful share of apparent model differences.
