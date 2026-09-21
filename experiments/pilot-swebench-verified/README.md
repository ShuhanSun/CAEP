# CAEP SWE-bench Verified Pilot

This pilot validates the repeated-run reliability pipeline before spending on a larger study.

## Design

- 5 fixed SWE-bench Verified tasks
- 1 coding agent
- 5 scored attempts per task
- 25 total scored trials
- deterministic benchmark verifier
- CAEP aggregation after every Harbor job

The selected tasks are fixed in `tasks.txt` instead of taking the first five tasks from a moving registry dataset. The pilot spans Django, Matplotlib, SymPy, and scikit-learn.

## Prerequisites

```bash
uv tool install harbor
python -m pip install -e .
export OPENAI_API_KEY=...
export CAEP_MODEL='<model supported by your Harbor/Codex setup>'
```

For local execution, Docker must be running. For a cloud sandbox, set `CAEP_ENV` and the corresponding provider credential.

## Run

```bash
bash experiments/pilot-swebench-verified/preflight.sh
bash experiments/pilot-swebench-verified/run.sh
```

Useful overrides:

```bash
CAEP_MODEL='your-model' \
CAEP_AGENT='codex' \
CAEP_ATTEMPTS=5 \
CAEP_CONCURRENCY=2 \
CAEP_ENV='docker' \
bash experiments/pilot-swebench-verified/run.sh
```

Outputs are written under `experiments/output/`, which is gitignored.

After the run:

- `experiments/output/caep-runs/` contains portable per-run CAEP evidence bundles with credential-bearing JSON and text evidence redacted for sharing.
- `experiments/output/report/aggregate.json` contains machine-readable repeated-run statistics.
- `experiments/output/report/reliability-report.md` contains the human-readable report.

## Pilot decision rule

Scale only if the pilot shows at least one of these signals:

1. mixed outcomes occur on one or more tasks;
2. cost-per-success materially differs from nominal run cost;
3. repeated runs expose meaningful cost or latency variance;
4. execution provenance reveals comparability problems worth formalizing.

If none occur, revise the hypothesis or task sample before spending more.
