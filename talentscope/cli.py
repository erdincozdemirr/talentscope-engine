# -*- coding: utf-8 -*-
import argparse
import json
from datetime import datetime
from pathlib import Path

from talentscope.pipeline import scan_pool


def _default_out_path(results_dir: str, job_file: str) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    job_stem = Path(job_file).stem
    return Path(results_dir) / f"{job_stem}_{ts}.json"


def main():
    p = argparse.ArgumentParser(description="TalentScope: CV–Job matching and candidate ranking engine.")
    p.add_argument("--pool", required=True, help="CV folder path (.pdf/.docx)")
    p.add_argument("--job", required=True, help="Job description file path (.txt/.pdf/.docx)")
    p.add_argument("--skills", required=True, help="skills.yaml path")
    p.add_argument("--salaries", default=None, help="salaries.csv path (optional)")
    p.add_argument("--min-fit", type=float, default=30.0, help="Reject if job_fit_score < this")
    p.add_argument("--top", type=int, default=10, help="Top N for known and unknown salary lists")
    p.add_argument("--results-dir", default="talentscope/results", help="Where to save JSON outputs")
    p.add_argument("--out", default=None, help="Optional explicit output JSON path")

    args = p.parse_args()

    output = scan_pool(
        cv_dir=args.pool,
        skills_yaml=args.skills,
        job_file=args.job,
        salaries_csv=args.salaries,
        min_fit_score=args.min_fit,
        top_n=args.top,
    )

    js = json.dumps(output, indent=2, ensure_ascii=False)
    print(js)

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    out_path = Path(args.out) if args.out else _default_out_path(str(results_dir), args.job)
    out_path.write_text(js, encoding="utf-8")


if __name__ == "__main__":
    main()
