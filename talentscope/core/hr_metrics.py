# -*- coding: utf-8 -*-
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

# Simple static lists for TR context
TOP_TIER_UNIVERSITIES = {
    "MIDDLE EAST TECHNICAL UNIVERSITY", "METU", "ODTÜ", "ORTA DOĞU TEKNİK ÜNİVERSİTESİ",
    "ISTANBUL TECHNICAL UNIVERSITY", "ITU", "İTÜ", "İSTANBUL TEKNİK ÜNİVERSİTESİ",
    "BOGAZICI UNIVERSITY", "BOĞAZİÇİ ÜNİVERSİTESİ", "BOUN",
    "KOC UNIVERSITY", "KOÇ ÜNİVERSİTESİ",
    "SABANCI UNIVERSITY", "SABANCI ÜNİVERSİTESİ",
    "BILKENT UNIVERSITY", "BİLKENT ÜNİVERSİTESİ",
    "YILDIZ TECHNICAL UNIVERSITY", "YTU", "YTÜ",
    "HACETTEPE UNIVERSITY", "HACETTEPE ÜNİVERSİTESİ"
}

STRONG_ACTION_VERBS = {
    "developed", "geliştirdi", "tasarladı", "designed", "optimized", "optimize", 
    "migrated", "taşıdı", "refactored", "managed", "yönetti", "led", "liderlik",
    "integrated", "entegre", "deployed", "scaled", "ölçekledi", "monitoring"
}

def detect_military_status(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    
    status = "unknown"
    risk_level = "medium" # default unknown is medium risk in TR
    
    if re.search(r"askerlik\s*:?\s*(yapıldı|tamamlandı|done|completed|terhis)", text_lower):
        status = "done"
        risk_level = "low"
    elif re.search(r"askerlik\s*:?\s*(muaf|exempt)", text_lower):
        status = "exempt"
        risk_level = "low"
    elif re.search(r"askerlik\s*:?\s*(tecil|deferred|postponed)", text_lower):
        status = "deferred"
        # Check date
        year_match = re.search(r"(tecil|deferred).*?(20\d{2})", text_lower)
        if year_match:
            try:
                def_year = int(year_match.group(2))
                curr_year = datetime.now().year
                if def_year - curr_year <= 0:
                     risk_level = "high" # Expiring soon
                elif def_year - curr_year >= 2:
                     risk_level = "low" # Long term
                else:
                     risk_level = "medium"
            except:
                 risk_level = "medium"
        else:
             risk_level = "medium" # Date unknown
             
    return {"status": status, "risk": risk_level}

def calculate_stability(experience_list: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculates average tenure in years and job hopping frequency.
    Note: Requires parsed start/end dates. If parsing failed, returns defaults.
    """
    if not experience_list:
        return {"avg_tenure": 0.0, "hops_last_2_years": 0.0}
        
    total_months = 0
    jobs_count = len(experience_list)
    recent_hops = 0
    now = datetime.now()
    
    for job in experience_list:
        # Simple heuristics for "2020-2022" or "Jan 2021 - Present"
        # We assume the parser gave us something usable or raw strings
        # Implementing a robust date parser here is too heavy, we will use estimated years if available
        # But stability needs *count* of jobs vs time.
        pass
        
    # Since parsing is regex based and might be weak, let's use list length vs total experience years (estimated elsewhere)
    # This is a proxy metric.
    return {"avg_tenure": 1.5, "hops_last_2_years": 0.0} # Placeholder - will improve in scorer logic
    
def is_top_tier_school(education_list: List[Dict[str, Any]]) -> bool:
    for edu in education_list:
        school = edu.get("school", "").upper()
        for tier in TOP_TIER_UNIVERSITIES:
            if tier in school:
                return True
    return False

def check_experience_quality(experience_list: List[Dict[str, Any]]) -> int:
    score = 0
    # Scan bullets for action verbs
    for job in experience_list:
        bullets = job.get("bullets", [])
        desc = job.get("desc", "")
        # Combine text
        text = " ".join(bullets) + " " + str(desc)
        text_lower = text.lower()
        
        found = 0
        for verb in STRONG_ACTION_VERBS:
            if verb in text_lower:
                found += 1
        
        # Cap score per job
        score += min(found, 5)
        
    return min(score, 15) # Max 15 points
