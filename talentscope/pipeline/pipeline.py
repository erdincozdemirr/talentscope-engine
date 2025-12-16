# -*- coding: utf-8 -*-
import math
import re
from collections import defaultdict
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from talentscope.core.normalize import norm
from talentscope.core.scoring import compute_job_match, detect_job_domains, score_domains
from talentscope.core.experience import estimate_experience_years
from talentscope.core.hr_scorer import HRScorer
from talentscope.io.extractors import extract_file_content, extract_resume_text
from talentscope.io.salary import load_salary_map_csv
from talentscope.skills.skills_loader import load_yaml


def _salary_mid_sort_key(rec: Dict[str, Any]) -> Tuple[float, float, float]:
    mid = rec.get("salary_mid_tl")
    smin = rec.get("salary_min_tl")
    smax = rec.get("salary_max_tl")
    return (
        mid if isinstance(mid, (int, float)) else math.inf,
        smin if isinstance(smin, (int, float)) else math.inf,
        smax if isinstance(smax, (int, float)) else math.inf,
    )


def _safe_stem(filename: str) -> str:
    stem = Path(filename).stem.lower().strip()
    stem = re.sub(r"\s+", "_", stem)
    stem = re.sub(r"[^a-z0-9_\-]+", "", stem)
    return stem or "candidate"


def _unique_candidate_id(filename: str, registry: Dict[str, int]) -> str:
    base = _safe_stem(filename)
    registry[base] += 1
    return base if registry[base] == 1 else f"{base}_{registry[base]}"


def scan_pool(
    cv_dir: str,
    skills_yaml: str,
    job_file: str,
    salaries_csv: Optional[str],
    min_fit_score: float,
    top_n: int,
) -> Dict[str, Any]:
    cfg = load_yaml(skills_yaml)

    job_text_raw = extract_file_content(job_file)
    job_text_norm = norm(job_text_raw)

    job_domains = detect_job_domains(job_text_norm, cfg)
    if not job_domains:
        raise ValueError("İş tanımında skills.yaml ile eşleşen bir domain bulunamadı.")

    filtered_domains = {k: v for k, v in cfg["domains"].items() if k in set(job_domains)}
    domain_cfg = {"domains": filtered_domains}

    salary_map = load_salary_map_csv(salaries_csv)

    files: List[str] = []
    for ext in ("*.pdf", "*.docx"):
        files.extend(glob(str(Path(cv_dir) / ext)))
    files = sorted(files)

    results: List[Dict[str, Any]] = []
    rejected = 0
    candidate_id_registry: Dict[str, int] = defaultdict(int)

    for fpath in files:
        fname = Path(fpath).name
        candidate_id = _unique_candidate_id(fname, candidate_id_registry)

        try:
            raw = extract_resume_text(fpath)
        except Exception:
            rejected += 1
            continue

        resume_text_norm = norm(raw)

        all_domain_scores = score_domains(resume_text_norm, cfg)
        overall_cv_score = sum(s for _, _, s in all_domain_scores)

        jm = compute_job_match(job_text_norm, resume_text_norm, domain_cfg)
        if "note" in jm:
            rejected += 1
            continue

        domain_cv_score_for_job = int(jm.get("resume_domain_score", 0))
        job_match_percent = float(jm["match_percent"])
        job_fit_score = round(domain_cv_score_for_job * (job_match_percent / 100.0), 2)

        if job_fit_score < min_fit_score:
            rejected += 1
            continue

        sal = salary_map.get(fname, {"min": None, "max": None})
        salary_min = sal.get("min")
        salary_max = sal.get("max")
        salary_expectation_val = str(salary_min) if salary_min else None
        
        salary_known = isinstance(salary_min, (int, float)) and isinstance(salary_max, (int, float))
        salary_mid = round((salary_min + salary_max) / 2.0, 2) if salary_known else None

        exp_years = estimate_experience_years(raw)

        # Prepare data for HR Scorer
        # Need "parsed" data structure which comes from CVParser (but here we only have raw text)
        # We need to run CVParser here to feed HRScorer properly
        from talentscope.core.parser import CVParser
        parser = CVParser(raw)
        parsed_data = parser.parse()
        
        # Skill injection logic similar to API (simplified)
        # Note: HRScorer needs skills to be in parsed_data["skills"] potentially, 
        # or it uses matches from compute_job_match.
        # HRScorer uses "top_matched_terms" from cv_data for evidence check.
        
        cv_data_for_hr = {
            "raw_text": raw,
            "parsed_data": parsed_data,
            "estimated_experience": exp_years,
            "top_matched_terms": [(t, w) for (t, w, _) in jm["matched_terms"]],
            "salary": salary_expectation_val, # Passed from somewhere else or parsed?
            # Actually we utilize "salary_min/max" from map
        }
        
        # Update salary in parsed data if known
        if salary_known:
             if salary_min == salary_max:
                 parsed_data["salary"] = salary_min
             else:
                 parsed_data["salary"] = f"{salary_min}-{salary_max}"

        # Job Data for Scorer
        # We need to pass job requirements (experience, salary limits if any)
        # Currently scan_pool params don't have exp limits, but we can pass generic defaults
        job_data_for_hr = {
            "title": Path(job_file).stem.replace("_", " "), # Guess title from filename
            "min_experience": 2, # Default
            "max_experience": 6, # Default 
            "min_salary": None,
            "max_salary": None
        }

        scorer = HRScorer(job_data_for_hr)
        hr_score_res = scorer.score(cv_data_for_hr)

        results.append(
            {
                "candidate_id": candidate_id,
                "candidate_file": fname,
                "estimated_experience": exp_years,
                "hr_score": hr_score_res["total_score"],
                "hr_score_details": hr_score_res["breakdown"],
                "hr_analysis": hr_score_res["details"],
                "job_domains": [{"domain": d, "label": cfg["domains"][d].get("label", d)} for d in job_domains],
                "overall_cv_score": overall_cv_score,
                "domain_cv_score_for_job": domain_cv_score_for_job,
                "job_match_percent": job_match_percent,
                "job_fit_score": job_fit_score,
                "salary_known": salary_known,
                "salary_min_tl": salary_min,
                "salary_max_tl": salary_max,
                "salary_mid_tl": salary_mid,
                "top_matched_terms": [(t, w) for (t, w, _) in jm["matched_terms"][:12]],
                "top_missing_terms": [(t, w) for (t, w, _) in jm["missing_terms"][:12]],
            }
        )

    known = [r for r in results if r["salary_known"]]
    unknown = [r for r in results if not r["salary_known"]]

    # Sort primarily by HR Score
    known.sort(key=lambda x: (-x["hr_score"], -x["job_fit_score"], *_salary_mid_sort_key(x)))
    unknown.sort(key=lambda x: (-x["hr_score"], -x["job_fit_score"]))

    known_top = known[:top_n]
    unknown_top = unknown[:top_n]

    for i, item in enumerate(known_top, start=1):
        item["rank"] = i
    for i, item in enumerate(unknown_top, start=1):
        item["rank"] = i

    return {
        "engine": "TalentScope",
        "timestamp": datetime.utcnow().isoformat(),
        "job": {
            "job_file": Path(job_file).name,
            "domains_detected": [{"domain": d, "label": cfg["domains"][d].get("label", d)} for d in job_domains],
            "minimum_threshold_job_fit_score": min_fit_score,
        },
        "pool": {
            "cv_dir": str(Path(cv_dir).resolve()),
            "total_cvs_scanned": len(files),
            "qualified_cvs": len(results),
            "qualified_salary_known": len(known),
            "qualified_salary_unknown": len(unknown),
            "rejected_cvs": rejected,
        },
        "results": {
            "salary_known_topN": known_top,
            "salary_unknown_topN": unknown_top,
        },
    }
