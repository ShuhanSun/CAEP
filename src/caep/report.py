from __future__ import annotations


def _pct(value):
    return "n/a" if value is None else f"{100 * value:.1f}%"


def _money(value):
    return "n/a" if value is None else f"${value:.2f}"


def render_markdown(aggregate: dict) -> str:
    lines = [
        "# CAEP Reliability Report",
        "",
        "## Summary",
        "",
        f"- Runs: {aggregate.get('runs', 0)}",
        f"- Successful runs: {aggregate.get('successful_runs', 0)}",
        f"- Success rate: {_pct(aggregate.get('success_rate'))}",
        f"- Cost coverage: {_pct(aggregate.get('cost_coverage'))}",
        f"- Nominal run cost: {_money(aggregate.get('mean_known_run_cost_usd'))}",
        f"- Cost per success: {_money(aggregate.get('cost_per_success_usd'))}",
        f"- Mixed-outcome task fraction: {_pct(aggregate.get('stability', {}).get('mixed_outcome_task_fraction'))}",
        "",
        "## Task stability",
        "",
        "| Task | Runs | Successes | Success rate | Outcome class | Entropy (bits) | Cost CV | Latency CV |",
        "|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for tid, row in aggregate.get("tasks", {}).items():
        entropy = row.get("outcome_entropy_bits")
        cost_cv = row.get("cost_cv")
        latency_cv = row.get("latency_cv")
        lines.append(
            f"| {tid} | {row.get('runs', 0)} | {row.get('successes', 0)} | "
            f"{_pct(row.get('success_rate'))} | {row.get('outcome_class', 'n/a')} | "
            f"{'n/a' if entropy is None else f'{entropy:.3f}'} | "
            f"{'n/a' if cost_cv is None else f'{cost_cv:.3f}'} | "
            f"{'n/a' if latency_cv is None else f'{latency_cv:.3f}'} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "`mixed_outcome` means the same task succeeded in some clean repetitions and failed in others. "
        "CAEP reports this directly instead of collapsing it into a single pass/fail label.",
        "",
        "Outcome entropy is 0 bits for perfectly consistent outcomes and approaches 1 bit when success/failure "
        "is maximally mixed. It is descriptive, not a composite quality score.",
        "",
    ]
    return "\n".join(lines)
