# CAEP v0.2-draft

## 1. Scope

CAEP standardizes provenance, evidence and repeated-run reliability for coding-agent evaluations.

CAEP MUST NOT redefine an existing trajectory standard when a conforming ATIF trajectory is available.

## 2. Required run bundle

A CAEP v0.2 run bundle MUST contain:

- `runspec.json`
- `result.json`
- `evidence-manifest.json`

A Harbor-derived bundle SHOULD also contain or reference:

- `trajectory.json` — native ATIF trajectory
- verifier reward
- native Harbor trial result
- native Harbor trial config

## 3. Run identity

A run is not identified solely by model name. A materially comparable execution identity SHOULD include:

- benchmark + benchmark version
- task ID + immutable task/repository revision when available
- agent + agent version
- model provider + model identifier/version when available
- harness + harness version
- environment/runtime identity
- timeout/resource/network policy
- relevant prompt/config digests

Unknown values MUST remain null or be marked unavailable. They MUST NOT be invented.

## 4. Success

Success MUST be derived from an explicit verifier or benchmark reward policy.

For Harbor imports, CAEP v0.2 accepts a numeric reward and a configured success threshold.
The importer records both the observed reward and threshold.

## 5. Cost per success

For a comparable run set S:

`cost_per_success = sum(run_cost for every run in S) / count(successful runs in S)`

Failed attempts MUST remain in the numerator.

When no successful runs exist, `cost_per_success` MUST be null.

When monetary cost is unknown for any run, implementations SHOULD report cost coverage and MUST NOT silently
treat unknown cost as zero.

## 6. Repeated-run reliability

CAEP reports:

- number of runs
- number of successful runs
- success rate
- observed pass@k for the actually observed k runs
- Wilson 95% confidence interval for success rate

"Observed pass@k" is deliberately distinguished from an estimator of pass@k over hypothetical samples.

## 7. Evidence integrity

Every locally included artifact MUST have a SHA-256 digest in `evidence-manifest.json`.

Verification checks content integrity only. It does not prove that the artifact was honestly generated.

## 8. ATIF

When `agent/trajectory.json` conforms to ATIF, CAEP SHOULD preserve it byte-for-byte and record its digest.

CAEP MAY derive token/cost fields from ATIF `final_metrics`, but MUST preserve the native artifact as evidence.

## 9. Recovery

Recovery is not a generic v0.2 metric because a sequence of retries is not sufficient to infer semantic
recovery. Future CAEP versions will define explicit failure/recovery annotations referencing ATIF step IDs
and verifier evidence.

## 10. Non-goals

v0.2 does not define:

- a new agent trajectory schema
- a benchmark task format
- sandbox orchestration
- a universal leaderboard score
- safety or quality weights
- an LLM-as-judge policy
