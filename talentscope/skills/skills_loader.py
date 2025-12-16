# -*- coding: utf-8 -*-
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from talentscope.core.normalize import norm


@dataclass(frozen=True)
class SkillItem:
    domain_key: str
    domain_label: str
    canonical: str
    weight: int
    kind: str
    variants_norm: Tuple[str, ...]


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _infer_kind(canon: str) -> str:
    c = canon or ""
    return "phrase" if (" " in c or "-" in c) else "token"


def load_yaml(skills_yaml: str) -> Dict[str, Any]:
    p = Path(skills_yaml)
    if not p.exists():
        raise FileNotFoundError(f"skills.yaml not found: {skills_yaml}")

    raw = yaml.safe_load(p.read_text(encoding="utf-8", errors="ignore")) or {}
    domains_raw = raw.get("domains")
    if not isinstance(domains_raw, dict):
        raise ValueError("skills.yaml must have a top-level 'domains' mapping.")

    out_domains: Dict[str, Any] = {}

    for domain_key, domain in domains_raw.items():
        domain = domain or {}
        domain_label = str(domain.get("label", domain_key))

        items_raw = domain.get("items") or []
        if not isinstance(items_raw, list):
            items_raw = []

        phrase_variant_set = set()
        phrase_items: List[SkillItem] = []
        token_items_raw: List[Dict[str, Any]] = []

        for it in items_raw:
            if not isinstance(it, dict):
                continue

            canonical = str(it.get("canonical") or "").strip()
            if not canonical:
                continue

            weight = int(it.get("weight") or 1)
            kind = str(it.get("kind") or "").strip().lower()
            if kind not in ("phrase", "token"):
                kind = _infer_kind(canonical)

            synonyms = [str(s).strip() for s in _as_list(it.get("synonyms")) if str(s).strip()]
            variants = [canonical] + synonyms
            variants_norm = [norm(v) for v in variants if norm(v)]
            variants_norm = sorted(set(variants_norm), key=len, reverse=True)
            if not variants_norm:
                continue

            canon_norm = norm(canonical)

            if kind == "phrase":
                for v in variants_norm:
                    phrase_variant_set.add(v)
                phrase_items.append(
                    SkillItem(
                        domain_key=domain_key,
                        domain_label=domain_label,
                        canonical=canon_norm,
                        weight=weight,
                        kind="phrase",
                        variants_norm=tuple(variants_norm),
                    )
                )
            else:
                token_items_raw.append(
                    {
                        "canonical": canonical,
                        "canon_norm": canon_norm,
                        "weight": weight,
                        "variants_norm": variants_norm,
                    }
                )

        token_items: List[SkillItem] = []
        for tk in token_items_raw:
            canon_norm = tk["canon_norm"]
            if canon_norm in phrase_variant_set:
                continue

            variants_norm = [v for v in tk["variants_norm"] if v not in phrase_variant_set]
            if not variants_norm:
                continue

            token_items.append(
                SkillItem(
                    domain_key=domain_key,
                    domain_label=domain_label,
                    canonical=canon_norm,
                    weight=int(tk["weight"]),
                    kind="token",
                    variants_norm=tuple(variants_norm),
                )
            )

        merged_items = phrase_items + token_items
        merged_items.sort(key=lambda x: (0 if x.kind == "phrase" else 1, -len(x.canonical), x.canonical))

        out_domains[domain_key] = {"label": domain_label, "items": merged_items}

    return {"domains": out_domains}
