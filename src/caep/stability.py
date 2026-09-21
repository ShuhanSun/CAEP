from __future__ import annotations
from math import log2
from statistics import mean, pstdev


def outcome_profile(successes: int, runs: int) -> dict:
    if runs <= 0:
        return {
            "outcome_class": "no_runs",
            "success_rate": None,
            "outcome_entropy_bits": None,
        }
    p = successes / runs
    if successes == runs:
        cls = "consistent_success"
    elif successes == 0:
        cls = "consistent_failure"
    else:
        cls = "mixed_outcome"
    entropy = 0.0
    for q in (p, 1.0 - p):
        if q > 0:
            entropy -= q * log2(q)
    return {
        "outcome_class": cls,
        "success_rate": p,
        "outcome_entropy_bits": entropy,
    }


def coefficient_of_variation(values: list[float]) -> float | None:
    values = [float(v) for v in values if v is not None]
    if len(values) < 2:
        return None
    m = mean(values)
    if m == 0:
        return None
    return pstdev(values) / abs(m)
