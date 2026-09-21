#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

MODEL="${CAEP_MODEL:-}"
AGENT="${CAEP_AGENT:-codex}"
ATTEMPTS="${CAEP_ATTEMPTS:-5}"
CONCURRENCY="${CAEP_CONCURRENCY:-2}"
ENVIRONMENT="${CAEP_ENV:-docker}"
TASK_FILE="${CAEP_TASK_FILE:-experiments/pilot-swebench-verified/tasks.txt}"
OUTPUT_ROOT="${CAEP_OUTPUT_ROOT:-experiments/output}"
JOBS_DIR="$OUTPUT_ROOT/harbor-jobs"
RUNS_DIR="$OUTPUT_ROOT/caep-runs"
REPORT_DIR="$OUTPUT_ROOT/report"

if [[ -z "$MODEL" ]]; then
  echo "ERROR: CAEP_MODEL must be set to the model identifier used by Harbor." >&2
  exit 2
fi

if ! command -v harbor >/dev/null 2>&1; then
  echo "ERROR: harbor is not installed. Install it with: uv tool install harbor" >&2
  exit 2
fi

if [[ ! -f "$TASK_FILE" ]]; then
  echo "ERROR: task file not found: $TASK_FILE" >&2
  exit 2
fi

mkdir -p "$JOBS_DIR" "$RUNS_DIR" "$REPORT_DIR"
python -m pip install -e . >/dev/null

echo "CAEP pilot"
echo "  agent:       $AGENT"
echo "  model:       $MODEL"
echo "  attempts:    $ATTEMPTS per task"
echo "  concurrency: $CONCURRENCY"
echo "  environment: $ENVIRONMENT"
echo "  task file:   $TASK_FILE"
echo

while IFS= read -r task || [[ -n "$task" ]]; do
  [[ -z "$task" ]] && continue
  [[ "$task" =~ ^# ]] && continue

  slug="$(printf '%s' "$task" | tr '/:' '--' | tr -cd '[:alnum:]_.-')"
  job_name="caep-pilot-${slug}"

  echo "=== Running $task ==="
  harbor run     -t "$task"     -a "$AGENT"     -m "$MODEL"     -k "$ATTEMPTS"     -n "$CONCURRENCY"     -e "$ENVIRONMENT"     --job-name "$job_name"     -o "$JOBS_DIR"     --yes

  job_path="$JOBS_DIR/$job_name"
  if [[ ! -d "$job_path" ]]; then
    echo "ERROR: Harbor completed but expected job directory was not found: $job_path" >&2
    exit 3
  fi

  task_runs_dir="$RUNS_DIR/$slug"
  rm -rf "$task_runs_dir"
  python -m caep import-harbor "$job_path" --out "$task_runs_dir"
  echo
done < "$TASK_FILE"

python -m caep aggregate "$RUNS_DIR" --out "$REPORT_DIR/aggregate.json" >/dev/null
python -m caep report "$REPORT_DIR/aggregate.json" --out "$REPORT_DIR/reliability-report.md" >/dev/null

echo
echo "Pilot complete."
echo "Aggregate: $REPORT_DIR/aggregate.json"
echo "Report:    $REPORT_DIR/reliability-report.md"
