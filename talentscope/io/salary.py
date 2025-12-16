# -*- coding: utf-8 -*-
import csv
import re
from pathlib import Path
from typing import Dict, Optional, Tuple


def _num(s: str) -> Optional[float]:
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    s = s.replace(" ", "")
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(".", "").replace(",", "")
    try:
        return float(s)
    except Exception:
        return None


def parse_salary_range(value: str) -> Tuple[Optional[float], Optional[float]]:
    if value is None:
        return (None, None)
    v = str(value).strip()
    if not v:
        return (None, None)
    v = v.replace("–", "-").replace("—", "-")
    v = re.sub(r"(tl|₺|try)", "", v, flags=re.IGNORECASE).strip()

    if "-" in v:
        parts = [p.strip() for p in v.split("-") if p.strip()]
        if len(parts) >= 2:
            a, b = _num(parts[0]), _num(parts[1])
            if a is None and b is None:
                return (None, None)
            if a is None:
                return (b, b)
            if b is None:
                return (a, a)
            return (min(a, b), max(a, b))

    a = _num(v)
    return (a, a) if a is not None else (None, None)


def load_salary_map_csv(path: Optional[str]) -> Dict[str, Dict[str, Optional[float]]]:
    mp: Dict[str, Dict[str, Optional[float]]] = {}
    if not path:
        return mp
    p = Path(path)
    if not p.exists():
        return mp

    with p.open("r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.DictReader(f)
        cols = set((reader.fieldnames or []))

        for row in reader:
            fname = (row.get("filename") or "").strip()
            if not fname:
                continue

            sal_min = sal_max = None
            if "salary_min_tl" in cols or "salary_max_tl" in cols:
                sal_min = _num(row.get("salary_min_tl") or "")
                sal_max = _num(row.get("salary_max_tl") or "")
                if sal_min is not None and sal_max is None:
                    sal_max = sal_min
                if sal_min is None and sal_max is not None:
                    sal_min = sal_max
            elif "salary_tl" in cols:
                sal_min, sal_max = parse_salary_range(row.get("salary_tl") or "")

            mp[fname] = {"min": sal_min, "max": sal_max}

    return mp


def append_salary_to_csv(csv_path: Path, filename: str, salary_input: str) -> None:
    """Appends filename and salary input (raw string) to the CSV."""
    file_exists = csv_path.exists()
    
    with csv_path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["filename", "salary_tl"])
        
        writer.writerow([filename, salary_input])
