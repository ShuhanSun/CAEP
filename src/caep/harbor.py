from __future__ import annotations
from pathlib import Path
import shutil
from typing import Any

from .redact import redact_json, redact_text
from .util import load_json, dump_json, sha256_file, safe_id


def _deep_get(obj: Any, *paths, default=None):
    for path in paths:
        cur = obj
        ok = True
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur is not None:
            return cur
    return default


def _read_reward(trial_dir: Path):
    txt = trial_dir / "verifier" / "reward.txt"
    if txt.is_file():
        try:
            return float(txt.read_text().strip())
        except Exception:
            pass

    js = trial_dir / "verifier" / "reward.json"
    if js.is_file():
        try:
            obj = load_json(js)
            if isinstance(obj, (int, float)):
                return float(obj)
            if isinstance(obj, dict):
                for key in ("reward", "score", "accuracy"):
                    if isinstance(obj.get(key), (int, float)):
                        return float(obj[key])
        except Exception:
            pass

    result = trial_dir / "result.json"
    if result.is_file():
        try:
            obj = load_json(result)
            value = _deep_get(
                obj,
                "reward",
                "score",
                "metrics.reward",
                "verifier.reward",
                "result.reward",
            )
            if isinstance(value, (int, float)):
                return float(value)
        except Exception:
            pass

    return None


def _trajectory_metrics(trial_dir: Path):
    candidates = [
        trial_dir / "agent" / "trajectory.json",
        trial_dir / "trajectory.json",
    ]
    p = next((candidate for candidate in candidates if candidate.is_file()), None)
    if p is None:
        return None, {
            "total_cost_usd": None,
            "input_tokens": None,
            "output_tokens": None,
            "cached_tokens": None,
        }

    try:
        obj = load_json(p)
        fm = obj.get("final_metrics") or {}
        metrics = {
            "total_cost_usd": fm.get("total_cost_usd"),
            "input_tokens": fm.get("total_prompt_tokens"),
            "output_tokens": fm.get("total_completion_tokens"),
            "cached_tokens": fm.get("total_cached_tokens"),
        }
        return p, metrics
    except Exception:
        return p, {
            "total_cost_usd": None,
            "input_tokens": None,
            "output_tokens": None,
            "cached_tokens": None,
        }


def _candidate_trial_dirs(job_dir: Path):
    """Discover Harbor trial directories across current and legacy layouts."""
    dirs = set()
    trials_root = job_dir / "trials"
    roots = [trials_root] if trials_root.exists() else [job_dir]

    for root in roots:
        for p in root.rglob("result.json"):
            if p.parent != job_dir:
                dirs.add(p.parent)
        for p in root.rglob("reward.txt"):
            candidate = p.parent.parent if p.parent.name == "verifier" else p.parent
            if candidate != job_dir:
                dirs.add(candidate)
        for p in root.rglob("reward.json"):
            candidate = p.parent.parent if p.parent.name == "verifier" else p.parent
            if candidate != job_dir:
                dirs.add(candidate)
        for p in root.rglob("trajectory.json"):
            candidate = p.parent.parent if p.parent.name == "agent" else p.parent
            if candidate != job_dir:
                dirs.add(candidate)

    return sorted(dirs)


def _extract_identity(job_dir: Path, trial_dir: Path):
    job_cfg = {}
    trial_cfg = {}

    if (job_dir / "config.json").is_file():
        try:
            job_cfg = load_json(job_dir / "config.json")
        except Exception:
            pass

    if (trial_dir / "config.json").is_file():
        try:
            trial_cfg = load_json(trial_dir / "config.json")
        except Exception:
            pass

    task_id = str(
        _deep_get(
            trial_cfg,
            "task.name",
            "task.id",
            "task_name",
            "task_id",
            "name",
            default=trial_dir.name,
        )
    )
    benchmark = _deep_get(
        trial_cfg,
        "dataset.name",
        "dataset",
        "benchmark",
        default=_deep_get(job_cfg, "dataset.name", "dataset", "benchmark", default=None),
    )
    benchmark_version = _deep_get(
        trial_cfg,
        "dataset.version",
        "dataset_version",
        "benchmark_version",
        default=_deep_get(
            job_cfg,
            "dataset.version",
            "dataset_version",
            "benchmark_version",
            default=None,
        ),
    )
    agent = str(
        _deep_get(
            trial_cfg,
            "agent.name",
            "agent",
            "agent_name",
            default=_deep_get(job_cfg, "agent.name", "agent", "agent_name", default="unknown"),
        )
    )
    model = str(
        _deep_get(
            trial_cfg,
            "model.name",
            "model",
            "model_name",
            default=_deep_get(job_cfg, "model.name", "model", "model_name", default="unknown"),
        )
    )
    provider = model.split("/", 1)[0] if "/" in model else None

    return {
        "task_id": task_id,
        "benchmark": benchmark if isinstance(benchmark, str) else None,
        "benchmark_version": str(benchmark_version) if benchmark_version is not None else None,
        "agent": agent,
        "model": model,
        "provider": provider,
    }


def import_harbor_job(job_dir: Path, out_dir: Path, success_threshold: float = 1.0):
    job_dir = job_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    imported = []

    for ordinal, trial_dir in enumerate(_candidate_trial_dirs(job_dir), 1):
        identity = _extract_identity(job_dir, trial_dir)
        reward = _read_reward(trial_dir)
        success = bool(reward is not None and reward >= success_threshold)
        trajectory_path, usage = _trajectory_metrics(trial_dir)

        native_result = {}
        if (trial_dir / "result.json").is_file():
            try:
                native_result = load_json(trial_dir / "result.json")
            except Exception:
                native_result = {}

        run_id = safe_id(
            f"{identity['task_id']}--{identity['agent']}--{identity['model']}--{ordinal:04d}"
        )
        bundle = out_dir / run_id
        bundle.mkdir(parents=True, exist_ok=False)

        runspec = {
            "protocol_version": "0.2-draft",
            "run_id": run_id,
            "source": {
                "type": "harbor",
                "native_trial_path": str(trial_dir.relative_to(job_dir)),
            },
            "task": {
                "benchmark": identity["benchmark"],
                "benchmark_version": identity["benchmark_version"],
                "task_id": identity["task_id"],
                "repository_revision": None,
            },
            "agent": {"name": identity["agent"], "version": None},
            "model": {
                "provider": identity["provider"],
                "name": identity["model"],
                "version": None,
            },
            "harness": {"name": "harbor", "version": None},
        }
        result = {
            "protocol_version": "0.2-draft",
            "run_id": run_id,
            "task_id": identity["task_id"],
            "success": success,
            "reward": {"value": reward, "success_threshold": success_threshold},
            "usage": usage,
            "timing": {
                "wall_time_seconds": _deep_get(
                    native_result,
                    "timing.wall_time_seconds",
                    "wall_time_seconds",
                    "duration_seconds",
                    "duration_sec",
                    default=None,
                )
            },
        }

        dump_json(bundle / "runspec.json", runspec)
        dump_json(bundle / "result.json", result)

        artifacts = []

        def copy_evidence(src: Path, dst_name: str, role: str, required=False):
            if not src.is_file():
                return
            dst = bundle / dst_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            artifacts.append(
                {
                    "path": dst_name,
                    "sha256": sha256_file(dst),
                    "role": role,
                    "required_for_judgment": bool(required),
                }
            )

        def copy_redacted_json(src: Path, dst_name: str, role: str, required=False):
            if not src.is_file():
                return
            original_sha256 = sha256_file(src)
            dst = bundle / dst_name
            try:
                obj = load_json(src)
            except Exception:
                # Do not silently drop malformed JSON evidence. Preserve the
                # original bytes when possible while still applying text-level
                # credential redaction as a safe fallback.
                original_bytes = src.read_bytes()
                original_text = original_bytes.decode("utf-8", errors="surrogateescape")
                cleaned = redact_text(original_text)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(cleaned.encode("utf-8", errors="surrogateescape"))
                artifacts.append(
                    {
                        "path": dst_name,
                        "sha256": sha256_file(dst),
                        "source_sha256": original_sha256,
                        "role": role,
                        "required_for_judgment": bool(required),
                        "sanitized": True,
                        "sanitization_mode": "text_fallback",
                    }
                )
                return
            dump_json(dst, redact_json(obj))
            artifacts.append(
                {
                    "path": dst_name,
                    "sha256": sha256_file(dst),
                    "source_sha256": original_sha256,
                    "role": role,
                    "required_for_judgment": bool(required),
                    "sanitized": True,
                }
            )

        def copy_redacted_text(src: Path, dst_name: str, role: str, required=False):
            if not src.is_file():
                return
            original_bytes = src.read_bytes()
            original_sha256 = sha256_file(src)
            original_text = original_bytes.decode("utf-8", errors="surrogateescape")
            cleaned = redact_text(original_text)
            if cleaned == original_text:
                copy_evidence(src, dst_name, role, required)
                return
            dst = bundle / dst_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(cleaned.encode("utf-8", errors="surrogateescape"))
            artifacts.append(
                {
                    "path": dst_name,
                    "sha256": sha256_file(dst),
                    "source_sha256": original_sha256,
                    "role": role,
                    "required_for_judgment": bool(required),
                    "sanitized": True,
                }
            )

        if trajectory_path:
            copy_redacted_json(trajectory_path, "native/trajectory.json", "atif_trajectory", False)

        copy_redacted_json(
            trial_dir / "config.json",
            "native/trial-config.json",
            "sanitized_harbor_trial_config",
            False,
        )
        copy_redacted_json(
            trial_dir / "result.json",
            "native/trial-result.json",
            "sanitized_harbor_trial_result",
            True,
        )
        copy_evidence(
            trial_dir / "verifier" / "reward.txt",
            "native/reward.txt",
            "verifier_reward",
            True,
        )
        copy_redacted_json(
            trial_dir / "verifier" / "reward.json",
            "native/reward.json",
            "verifier_reward",
            True,
        )
        copy_redacted_text(
            trial_dir / "verifier" / "test-stdout.txt",
            "native/test-stdout.txt",
            "verifier_stdout",
            False,
        )
        copy_redacted_text(
            trial_dir / "verifier" / "test-stderr.txt",
            "native/test-stderr.txt",
            "verifier_stderr",
            False,
        )

        for name, role in (("runspec.json", "caep_runspec"), ("result.json", "caep_result")):
            artifacts.append(
                {
                    "path": name,
                    "sha256": sha256_file(bundle / name),
                    "role": role,
                    "required_for_judgment": name == "result.json",
                }
            )

        manifest = {
            "protocol_version": "0.2-draft",
            "run_id": run_id,
            "artifacts": artifacts,
            "omissions": [
                {
                    "artifact": "raw Harbor config/result JSON",
                    "reason": "credential-bearing fields are sanitized before portable evidence is written",
                }
            ],
        }
        dump_json(bundle / "evidence-manifest.json", manifest)
        imported.append(bundle)

    return imported
