# -*- coding: utf-8 -*-
import re


def norm(text: str) -> str:
    t = (text or "").lower()
    t = t.replace("\u00a0", " ")
    t = re.sub(r"[^\w]+", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def boundary_pattern(needle_norm: str) -> str:
    return rf"(?<!\w){re.escape(needle_norm)}(?!\w)"
