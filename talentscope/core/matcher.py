# -*- coding: utf-8 -*-
import re
from typing import Dict, List, Tuple

from talentscope.core.normalize import boundary_pattern
from talentscope.skills.skills_loader import SkillItem


def compile_patterns(items: List[SkillItem]) -> Dict[str, List[Tuple[SkillItem, re.Pattern]]]:
    compiled: Dict[str, List[Tuple[SkillItem, re.Pattern]]] = {"phrase": [], "token": []}

    for it in items:
        variants = sorted(set(it.variants_norm), key=len, reverse=True)
        alts = "|".join(boundary_pattern(v) for v in variants if v)
        if not alts:
            continue
        compiled[it.kind].append((it, re.compile(alts, flags=re.IGNORECASE | re.UNICODE)))

    return compiled


def find_phrase_spans(text_norm: str, compiled_phrases: List[Tuple[SkillItem, re.Pattern]]) -> List[Tuple[int, int]]:
    spans: List[Tuple[int, int]] = []
    for _, pat in compiled_phrases:
        for m in pat.finditer(text_norm):
            spans.append((m.start(), m.end()))
    spans.sort()

    merged: List[Tuple[int, int]] = []
    for s, e in spans:
        if not merged or s > merged[-1][1]:
            merged.append((s, e))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))

    return merged


def span_contains(spans: List[Tuple[int, int]], idx: int) -> bool:
    for s, e in spans:
        if s <= idx < e:
            return True
        if idx < s:
            return False
    return False


def score_text(
    text_norm: str,
    items: List[SkillItem],
    compiled: Dict[str, List[Tuple[SkillItem, re.Pattern]]],
) -> Tuple[int, List[Tuple[str, int, str]]]:
    phrase_spans = find_phrase_spans(text_norm, compiled["phrase"])
    matched: Dict[str, Tuple[int, str]] = {}

    for it, pat in compiled["phrase"]:
        if it.canonical in matched:
            continue
        if pat.search(text_norm):
            matched[it.canonical] = (it.weight, it.domain_label)

    for it, pat in compiled["token"]:
        if it.canonical in matched:
            continue
        for m in pat.finditer(text_norm):
            if not span_contains(phrase_spans, m.start()):
                matched[it.canonical] = (it.weight, it.domain_label)
                break

    matched_list = [(c, w, d) for c, (w, d) in matched.items()]
    matched_list.sort(key=lambda x: (-x[1], x[0]))
    score = sum(w for _, w, _ in matched_list)
    return score, matched_list
