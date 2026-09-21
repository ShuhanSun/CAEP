from __future__ import annotations
from pathlib import Path
from .util import load_json, sha256_file

def verify_bundle(bundle: Path):
    manifest_path = bundle / "evidence-manifest.json"
    manifest = load_json(manifest_path)
    checks = []
    ok = True
    for a in manifest.get("artifacts", []):
        p = bundle / a["path"]
        exists = p.is_file()
        digest = sha256_file(p) if exists else None
        matches = exists and digest == a["sha256"]
        checks.append({
            "path":a["path"],
            "exists":exists,
            "sha256_matches":matches,
        })
        ok = ok and matches
    return {"ok":ok,"checks":checks}
