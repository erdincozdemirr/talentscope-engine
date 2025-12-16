# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Tuple

from talentscope.core.matcher import compile_patterns, score_text
from talentscope.skills.skills_loader import SkillItem


def _domain_items(domain_cfg: Dict[str, Any]) -> List[SkillItem]:
    items = domain_cfg.get("items") or domain_cfg.get("skills") or []
    return items if isinstance(items, list) else []


def score_domains(text_norm: str, cfg: Dict[str, Any]) -> List[Tuple[str, str, int]]:
    out: List[Tuple[str, str, int]] = []
    domains = (cfg or {}).get("domains") or {}
    for dk, dv in domains.items():
        label = (dv or {}).get("label", dk)
        items = _domain_items(dv or {})
        if not items:
            out.append((dk, label, 0))
            continue
        compiled = compile_patterns(items)
        s, _ = score_text(text_norm, items, compiled)
        out.append((dk, label, int(s)))
    out.sort(key=lambda x: (-x[2], x[0]))
    return out


def detect_job_domains(job_text_norm: str, cfg: Dict[str, Any]) -> List[str]:
    scored = score_domains(job_text_norm, cfg)
    return [d for (d, _, s) in scored if s > 0]


def compute_job_match(job_text_norm: str, resume_text_norm: str, domain_cfg: Dict[str, Any]) -> Dict[str, Any]:
    domains = (domain_cfg or {}).get("domains") or {}
    if not domains:
        return {"note": "no_domains"}

    job_total = 0
    matched_terms: List[Tuple[str, int, str]] = []
    missing_terms: List[Tuple[str, int, str]] = []
    resume_domain_score = 0

    for _, dv in domains.items():
        label = (dv or {}).get("label", "")
        items = _domain_items(dv or {})
        if not items:
            continue

        compiled = compile_patterns(items)

        job_score, job_hits = score_text(job_text_norm, items, compiled)
        res_score, res_hits = score_text(resume_text_norm, items, compiled)

        job_total += int(job_score)
        resume_domain_score += int(res_score)

        job_map = {c: (w, dlab) for (c, w, dlab) in job_hits}
        res_set = {c for (c, _, _) in res_hits}

        for c, (w, dlab) in job_map.items():
            if c in res_set:
                matched_terms.append((c, int(w), dlab or label))
            else:
                missing_terms.append((c, int(w), dlab or label))

    if job_total <= 0:
        return {"note": "job_has_no_weight"}

    matched_w = sum(w for (_, w, _) in matched_terms)
    match_percent = round((matched_w / job_total) * 100.0, 2)

    matched_terms.sort(key=lambda x: (-x[1], x[0]))
    missing_terms.sort(key=lambda x: (-x[1], x[0]))

    return {
        "match_percent": match_percent,
        "resume_domain_score": int(resume_domain_score),
        "matched_terms": matched_terms,
        "missing_terms": missing_terms,
        "job_total_weight": int(job_total),
        "matched_weight": int(matched_w),
    }
