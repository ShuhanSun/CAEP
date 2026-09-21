from __future__ import annotations
from math import sqrt
from pathlib import Path
from .util import load_json
from .stability import outcome_profile, coefficient_of_variation


def wilson_interval(successes: int, n: int, z: float = 1.959963984540054):
    if n <= 0:
        return [None, None]
    p = successes / n
    denom = 1 + (z*z)/n
    center = (p + (z*z)/(2*n)) / denom
    half = (z * sqrt((p*(1-p)/n) + (z*z)/(4*n*n))) / denom
    return [max(0.0, center-half), min(1.0, center+half)]


def discover_results(root: Path):
    if (root / "result.json").is_file():
        yield root / "result.json"
        return
    for p in sorted(root.rglob("result.json")):
        try:
            obj = load_json(p)
        except Exception:
            continue
        if obj.get("protocol_version") == "0.2-draft":
            yield p


def aggregate(root: Path):
    rows = [load_json(p) for p in discover_results(root)]
    n = len(rows)
    successes = sum(bool(r.get("success")) for r in rows)

    known_cost_rows = [r for r in rows if r.get("usage", {}).get("total_cost_usd") is not None]
    total_known_cost = sum(r["usage"]["total_cost_usd"] for r in known_cost_rows)
    full_cost_coverage = len(known_cost_rows) == n

    cps = None
    if successes > 0 and full_cost_coverage:
        cps = total_known_cost / successes

    tasks = {}
    for r in rows:
        tid = r.get("task_id") or r.get("task", {}).get("task_id") or "__unknown__"
        tasks.setdefault(tid, []).append(r)

    task_summaries = {}
    class_counts = {
        "consistent_success": 0,
        "consistent_failure": 0,
        "mixed_outcome": 0,
        "no_runs": 0,
    }
    for tid, rr in sorted(tasks.items()):
        tn = len(rr)
        ts = sum(bool(x.get("success")) for x in rr)
        profile = outcome_profile(ts, tn)
        class_counts[profile["outcome_class"]] += 1
        costs = [x.get("usage", {}).get("total_cost_usd") for x in rr]
        latencies = [x.get("timing", {}).get("wall_time_seconds") for x in rr]
        task_summaries[tid] = {
            "runs": tn,
            "successes": ts,
            "success_rate": (ts/tn if tn else None),
            "observed_pass_at_k": (1 if ts > 0 else 0) if tn else None,
            "k": tn,
            "success_rate_ci95_wilson": wilson_interval(ts, tn),
            "outcome_class": profile["outcome_class"],
            "outcome_entropy_bits": profile["outcome_entropy_bits"],
            "cost_cv": coefficient_of_variation(costs),
            "latency_cv": coefficient_of_variation(latencies),
        }

    task_count = len(task_summaries)
    mixed_fraction = (class_counts["mixed_outcome"] / task_count) if task_count else None

    return {
        "protocol_version": "0.2-draft",
        "runs": n,
        "successful_runs": successes,
        "success_rate": (successes/n if n else None),
        "success_rate_ci95_wilson": wilson_interval(successes, n),
        "observed_pass_at_k": (1 if successes > 0 else 0) if n else None,
        "k": n,
        "known_cost_runs": len(known_cost_rows),
        "cost_coverage": (len(known_cost_rows)/n if n else None),
        "total_known_cost_usd": total_known_cost if known_cost_rows else None,
        "cost_per_success_usd": cps,
        "stability": {
            "task_count": task_count,
            "outcome_class_counts": class_counts,
            "mixed_outcome_task_fraction": mixed_fraction,
        },
        "tasks": task_summaries,
    }
