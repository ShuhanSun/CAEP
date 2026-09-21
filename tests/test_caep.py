from pathlib import Path
import tempfile
from caep.harbor import import_harbor_job
from caep.aggregate import aggregate
from caep.verify import verify_bundle

FIXTURE = Path(__file__).parent / "fixtures" / "harbor-job"

def test_import_aggregate_and_verify():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "runs"
        bundles = import_harbor_job(FIXTURE, out, success_threshold=1.0)
        assert len(bundles) == 5
        for b in bundles:
            assert verify_bundle(b)["ok"]

        a = aggregate(out)
        assert a["runs"] == 5
        assert a["successful_runs"] == 3
        assert abs(a["success_rate"] - 0.6) < 1e-12
        assert abs(a["total_known_cost_usd"] - 19.09) < 1e-9
        assert abs(a["cost_per_success_usd"] - (19.09/3)) < 1e-9
        assert a["observed_pass_at_k"] == 1
        assert a["k"] == 5

def test_unknown_cost_is_not_treated_as_zero():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "runs"
        bundles = import_harbor_job(FIXTURE, out, success_threshold=1.0)
        import json
        p = bundles[0] / "result.json"
        obj = json.loads(p.read_text())
        obj["usage"]["total_cost_usd"] = None
        p.write_text(json.dumps(obj))
        a = aggregate(out)
        assert a["cost_coverage"] == 0.8
        assert a["cost_per_success_usd"] is None

from caep.stability import outcome_profile
from caep.report import render_markdown


def test_stability_profiles_are_threshold_free():
    assert outcome_profile(5, 5)["outcome_class"] == "consistent_success"
    assert outcome_profile(0, 5)["outcome_class"] == "consistent_failure"
    mixed = outcome_profile(3, 5)
    assert mixed["outcome_class"] == "mixed_outcome"
    assert 0.0 < mixed["outcome_entropy_bits"] <= 1.0


def test_aggregate_exposes_task_stability_and_report():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "runs"
        import_harbor_job(FIXTURE, out, success_threshold=1.0)
        a = aggregate(out)
        task = a["tasks"]["demo/reliability-task"]
        assert task["outcome_class"] == "mixed_outcome"
        assert a["stability"]["mixed_outcome_task_fraction"] == 1.0
        assert task["cost_cv"] is not None
        report = render_markdown(a)
        assert "mixed_outcome" in report
        assert "Cost per success" in report
