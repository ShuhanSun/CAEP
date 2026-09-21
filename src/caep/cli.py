from __future__ import annotations
import argparse
from pathlib import Path
import json
from .harbor import import_harbor_job
from .aggregate import aggregate
from .verify import verify_bundle
from .util import dump_json, load_json
from .report import render_markdown

def main(argv=None):
    parser = argparse.ArgumentParser(prog="caep")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("import-harbor", help="Import a completed Harbor job into CAEP bundles")
    p.add_argument("job_dir", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--success-threshold", type=float, default=1.0)

    p = sub.add_parser("aggregate", help="Aggregate CAEP run bundles")
    p.add_argument("runs_dir", type=Path)
    p.add_argument("--out", type=Path)

    p = sub.add_parser("verify", help="Verify evidence hashes for one CAEP bundle")
    p.add_argument("bundle_dir", type=Path)

    p = sub.add_parser("report", help="Render a Markdown reliability report from aggregate JSON")
    p.add_argument("aggregate_json", type=Path)
    p.add_argument("--out", type=Path)

    args = parser.parse_args(argv)

    if args.command == "import-harbor":
        imported = import_harbor_job(args.job_dir, args.out, args.success_threshold)
        print(json.dumps({"imported":len(imported),"out":str(args.out)}, indent=2))
        return 0
    if args.command == "aggregate":
        result = aggregate(args.runs_dir)
        if args.out:
            dump_json(args.out, result)
        print(json.dumps(result, indent=2))
        return 0
    if args.command == "verify":
        result = verify_bundle(args.bundle_dir)
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 2
    if args.command == "report":
        report = render_markdown(load_json(args.aggregate_json))
        if args.out:
            args.out.write_text(report + "\n", encoding="utf-8")
        print(report)
        return 0
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
