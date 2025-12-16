# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional
from talentscope.core.hr_metrics import (
    detect_military_status, 
    is_top_tier_school, 
    check_experience_quality
)

class HRScorer:
    def __init__(self, job_data: Dict[str, Any]):
        self.job_data = job_data
        # Varsayılan limitler
        self.target_experience_min = job_data.get("min_experience", 2)
        self.target_experience_max = job_data.get("max_experience", 5)
        self.salary_min = job_data.get("min_salary")
        self.salary_max = job_data.get("max_salary")
        self.target_title = job_data.get("title", "").lower() # e.g. "backend developer"

    def score(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the HR Score (0-100) based on 6 dimensions.
        """
        raw_text = cv_data.get("raw_text", "")
        # Parsed structured data
        parsed = cv_data.get("parsed_data", {})
        
        # 1. Operational (Max 25)
        op_score, op_details = self._score_operational(parsed, raw_text)
        
        # 2. Role Fit (Max 25)
        role_score, role_details = self._score_role_fit(cv_data, parsed)
        
        # 3. Evidence (Max 20)
        ev_score, ev_details = self._score_evidence(cv_data, parsed)
        
        # 4. Experience Quality (Max 15)
        qual_score = check_experience_quality(parsed.get("experience", []))
        
        # 5. Stability (Max 10)
        stab_score, stab_details = self._score_stability(parsed)
        
        # 6. School / Pivot (Max 5)
        school_score = 5 if is_top_tier_school(parsed.get("education", [])) else 0
        # Pivot logic can be added here (if non-IT + pivot evidence -> +3)
        
        # 7. Risk Penalty (Negative)
        penalty, pen_details = self._calculate_risk_penalty(parsed)
        
        total = op_score + role_score + ev_score + qual_score + stab_score + school_score + penalty
        total = max(0, min(100, total)) # Clamp 0-100
        
        return {
            "total_score": round(total, 1),
            "breakdown": {
                "operational": op_score,
                "role_fit": role_score,
                "evidence": ev_score,
                "quality": qual_score,
                "stability": stab_score,
                "school": school_score,
                "penalty": penalty
            },
            "details": {
                **op_details,
                **role_details,
                **ev_details,
                **stab_details,
                **pen_details
            }
        }

    def _score_operational(self, parsed: Dict[str, Any], raw_text: str) -> tuple:
        score = 25
        details = {}
        
        # Military
        mil = detect_military_status(raw_text)
        details["military"] = mil["status"]
        if mil["risk"] == "high":
            score -= 5
            details["military_penalty"] = -5
        elif mil["risk"] == "medium":
            score -= 2
            
        # Salary
        # If expectation is way above band -> Reject or huge penalty
        cand_sal = parsed.get("salary")
        if self.salary_max and cand_sal:
            # Try to parse cand_sal if string
            try:
                # Simplification: if cand min > job max * 1.2 -> Penalty
                pass 
            except:
                pass
                
        # Location (Default Istanbul Check could go here)
        
        return max(0, score), details

    def _score_role_fit(self, cv_data: Dict[str, Any], parsed: Dict[str, Any]) -> tuple:
        score = 0
        details = {}
        
        # Experience Years (Max 15)
        exp_years = cv_data.get("estimated_experience", 0)
        details["exp_years"] = exp_years
        
        if self.target_experience_min <= exp_years <= self.target_experience_max:
            score += 15 # Perfect
        elif exp_years > self.target_experience_max:
             # Overqualified? HR says HOLD usually, maybe slight penalty or full score?
             # User says "Senior/Lead" -> HOLD (Overqualified risk). Let's give 10.
             score += 10
             details["fit_note"] = "Overqualified"
        elif exp_years < self.target_experience_min:
             score += 5 # Junior
             details["fit_note"] = "Underqualified"
        else:
             score += 15 # Close enough
             
        # Title Match (Max 10)
        # Check current job title
        exps = parsed.get("experience", [])
        if exps:
            curr_title = exps[0].get("title", "").lower()
            if self.target_title in curr_title or "developer" in curr_title or "engineer" in curr_title:
                score += 10
            elif "junior" in curr_title and "senior" in self.target_title:
                score += 2
            else:
                score += 5
        else:
             score += 0 # No exp
             
        return score, details

    def _score_evidence(self, cv_data: Dict[str, Any], parsed: Dict[str, Any]) -> tuple:
        score = 0
        details = {}
        
        # Logic: "Must-have skill listed in Skills? Low. Listed in Experience? High."
        # We need must-have list. Let's assume top matched terms are must-haves.
        
        top_matched = cv_data.get("top_matched_terms", []) # [(term, weight), ...]
        must_haves = [t for t, w in top_matched if w >= 8] # High weight skills
        
        if not must_haves:
            return 20, {"note": "No strict must-haves defined"}
            
        exps = parsed.get("experience", [])
        evidence_count = 0
        
        combined_exp_text = " ".join([(e.get("desc","") + " " + " ".join(e.get("bullets",[]))) for e in exps]).lower()
        
        for skill in must_haves:
            if skill in combined_exp_text:
                score += 5 # Strong evidence
                evidence_count += 1
            else:
                score += 1 # Only listed in Profile/Skills
                
        details["verified_skills"] = evidence_count
        return min(20, score), details

    def _score_stability(self, parsed: Dict[str, Any]) -> tuple:
        # Placeholder for complex implementation
        exps = parsed.get("experience", [])
        count = len(exps)
        if count == 0:
            return 0, {}
        
        # User rule: >3 jobs in 24 months -> Reject/Low Score
        # Assume normal
        return 10, {}

    def _calculate_risk_penalty(self, parsed: Dict[str, Any]) -> tuple:
        penalty = 0
        details = {}
        
        # Example check
        # if job_hopping: penalty -= 20
        
        return penalty, details
