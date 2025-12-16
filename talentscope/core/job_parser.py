# -*- coding: utf-8 -*-
import re
import json
from typing import Any, Dict, List, Optional
from pathlib import Path
from talentscope.core.normalize import norm

class JobParser:
    def __init__(self, raw_text: str, filename: str = "job_posting"):
        self.raw_text = raw_text
        self.norm_text = norm(raw_text)
        self.filename = filename
        
        # Basic Categorization Map (Hardcoded for prototype)
        self.skill_categories = {
            "methodologies": ["DDD", "Domain Driven Design", "SDLC", "Agile", "Scrum", "Kanban", "SOLID", "Clean Architecture", "TDD", "CI/CD"],
            "architecture": ["Microservices", "Microservice", "Monolith", "Layered Architecture", "Katmanlı", "SOA", "Enterprise", "Kurumsal"],
            "backend_stack": ["Java", "Spring", "Spring Boot", "Spring Cloud", "Hibernate", "JPA", "Rest", "SOAP", "API", "Python", "Go", "C#", ".NET", "Node.js"],
            "data_layer": ["SQL", "NoSQL", "Oracle", "MySQL", "PostgreSQL", "MongoDB", "Redis", "Hazelcast", "Elasticsearch", "Cassandra", "Kafka", "RabbitMQ"],
            "devops": ["Docker", "Kubernetes", "K8s", "Jenkins", "GitLab CI", "Git", "AWS", "Azure", "GCP", "Linux", "Terraform", "Ansible"],
            "frontend_basics": ["HTML", "CSS", "JavaScript", "React", "Angular", "Vue", "jQuery", "Typescript"]
        }

    def parse(self) -> Dict[str, Any]:
        """
        Main parsing method returning the detailed structure.
        """
        seniority = self._extract_seniority()
        tech = self._extract_tech_stack()
        eligibility = self._extract_eligibility()
        
        return {
            "job_id": self.filename,
            "job_title": self._extract_title(),
            "job_family": "Software Engineering", # Default
            "job_track": "Backend" if "Java" in self.raw_text or "Backend" in self.raw_text else "General",
            "seniority": seniority,
            "education": self._extract_education(),
            "eligibility": eligibility,
            "methodologies": tech.get("methodologies", {}),
            "architecture": tech.get("architecture", {}),
            "backend_stack": tech.get("backend_stack", {}),
            "data_layer": tech.get("data_layer", {}),
            "middleware_and_runtime": tech.get("middleware", {}),
            "caching": tech.get("caching", {}),
            "devops_and_delivery": tech.get("devops", {}),
            "messaging": tech.get("messaging", {}),
            "soft_skills": self._extract_soft_skills(),
            "scoring_rules": self._generate_scoring_rules(seniority["min_years_experience"]),
            "extraction_meta": {
                "language": "tr",
                "parser_version": "v1_hr_job_parser"
            }
        }

    def _extract_title(self) -> str:
        # First line is usually the title or filename
        lines = [l.strip() for l in self.raw_text.split('\n') if l.strip()]
        if lines:
            if len(lines[0]) < 100:
                return lines[0]
        return self.filename.replace("_", " ").title()

    def _extract_seniority(self) -> Dict[str, Any]:
        # Look for "X yıl", "X years", "en az X"
        min_years = 0
        evidence = []
        
        # Regex for years
        year_pattern = r"(en az|minimum)?\s*(\d+)\s*(yıl|sene|year)"
        matches = re.finditer(year_pattern, self.raw_text, re.IGNORECASE)
        
        for m in matches:
            val = int(m.group(2))
            # sanity check, usually < 15
            if val < 20: 
                min_years = max(min_years, val)
                # Find the full sentence or context
                start = max(0, m.start() - 20)
                end = min(len(self.raw_text), m.end() + 20)
                evidence.append(self.raw_text[start:end].replace("\n", " ").strip() + "...")
        
        target_level = "Junior"
        if min_years >= 5: target_level = "Senior"
        elif min_years >= 3: target_level = "Mid"
        
        if "Senior" in self.raw_text or "Kıdemli" in self.raw_text:
            target_level = "Senior"
            
        return {
            "target_level": target_level,
            "min_years_experience": min_years,
            "max_years_experience": None,
            "evidence": evidence or ["Derived from text analysis"]
        }

    def _extract_education(self) -> Dict[str, Any]:
        keywords = ["Mühendisliği", "Engineering", "Bilgisayar", "Computer", "Lisans", "Bachelor", "Degree"]
        
        required = False
        accepted = []
        
        for kw in keywords:
            if kw in self.raw_text:
                required = True
                if kw not in accepted: accepted.append(kw)
                
        return {
            "required": required,
            "accepted_majors": accepted if accepted else ["Related Fields"],
            "degree_level_min": "bachelor" if required else "unspecified"
        }

    def _extract_eligibility(self) -> Dict[str, Any]:
        mil_req = False
        mil_ev = []
        if "askerlik" in self.norm_text:
            mil_req = True
            # Find evidence clause
            idx = self.norm_text.find("askerlik")
            start = max(0, idx - 30)
            end = min(len(self.raw_text), idx + 50)
            mil_ev.append(self.raw_text[start:end].strip())
            
        work_model = "unspecified"
        if "remote" in self.norm_text or "uzaktan" in self.norm_text:
            work_model = "remote"
        elif "hibrit" in self.norm_text or "hybrid" in self.norm_text:
            work_model = "hybrid"
            
        return {
            "military_service": {
                "applies_to": "male_candidates",
                "required": mil_req,
                "evidence": mil_ev
            },
            "work_model": {
                "type": work_model
            }
        }

    def _extract_tech_stack(self) -> Dict[str, Any]:
        # Initialize buckets
        buckets = {
            "methodologies": {"required": [], "nice_to_have": []},
            "architecture": {"required": [], "nice_to_have": []},
            "backend_stack": {
                "required": {"languages": [], "frameworks": [], "apis": []},
                "nice_to_have": {}
            },
            "data_layer": {"required": [], "nice_to_have": []},
            "devops": {"required": [], "nice_to_have": []},
            "caching": {"required": [], "nice_to_have": []},
            "messaging": {"required": [], "nice_to_have": []},
            "middleware": {"required": [], "nice_to_have": []}
        }
        
        # Helper to find evidence
        sentences = self.raw_text.split('.')
        
        def find_evidence(term):
            for s in sentences:
                if term.lower() in s.lower():
                    return s.strip()
            return f"{term} mentioned in text"

        # Scan
        # 1. Methodologies
        for m in self.skill_categories["methodologies"]:
            if m.lower() in self.norm_text:
                buckets["methodologies"]["required"].append({
                    "name": m,
                    "weight": 5,
                    "evidence": [find_evidence(m)]
                })

        # 2. Architecture (Simple scan)
        for a in self.skill_categories["architecture"]:
            if a.lower() in self.norm_text:
                buckets["architecture"]["required"].append({
                    "name": a,
                    "weight": 6,
                    "evidence": [find_evidence(a)]
                })

        # 3. Backend Stack (Complex)
        # Scan explicitly for Java, Spring etc.
        if "java" in self.norm_text:
             buckets["backend_stack"]["required"]["languages"].append({"name": "Java", "weight": 10, "evidence": [find_evidence("Java")]})
        
        if "spring" in self.norm_text:
             comps = []
             for comp in ["Spring Boot", "Spring Cloud", "Spring Security"]:
                 if comp.lower() in self.norm_text:
                     comps.append(comp)
             buckets["backend_stack"]["required"]["frameworks"].append({
                 "name": "Spring Ecosystem", 
                 "components": comps, 
                 "weight": 10, 
                 "evidence": [find_evidence("Spring")]
             })
             
        if "rest" in self.norm_text or "soap" in self.norm_text:
             buckets["backend_stack"]["required"]["apis"].append({
                 "name": "Web Services",
                 "types": ["REST" if "rest" in self.norm_text else None, "SOAP" if "soap" in self.norm_text else None],
                 "weight": 8,
                 "evidence": [find_evidence("REST") or find_evidence("SOAP")]
             })

        # 4. Data Layer
        for d in self.skill_categories["data_layer"]:
             if d.lower() in self.norm_text:
                 # Check if caching or messaging
                 if d in ["Redis", "Hazelcast"]:
                     buckets["caching"]["required"].append({"name": d, "weight":6, "evidence": [find_evidence(d)]})
                 elif d in ["Kafka", "RabbitMQ"]:
                     buckets["messaging"]["nice_to_have"].append({"name": d, "weight":4, "evidence": [find_evidence(d)]})
                 else:
                     buckets["data_layer"]["required"].append({"name": d, "weight": 5, "evidence": [find_evidence(d)]})

        # 5. DevOps
        for d in self.skill_categories["devops"]:
            if d.lower() in self.norm_text:
                buckets["devops"]["required"].append({"name": d, "weight": 4, "evidence": [find_evidence(d)]})

        return buckets

    def _extract_soft_skills(self) -> Dict[str, Any]:
        softs = ["İletişim", "Takım çalışması", "Analitik", "Problem çözme", "Analiz"]
        found = []
        for s in softs:
            if s.lower() in self.norm_text:
                found.append({"name": s, "weight": 3, "evidence": [f"{s} mentioned"]})
        return {"required": found, "nice_to_have": []}

    def _generate_scoring_rules(self, min_years: int) -> Dict[str, Any]:
        rules = []
        if min_years > 0:
            rules.append({
                "rule_id": f"HF_EXP_MIN_{min_years}Y",
                "type": "experience_years_min",
                "min_years": min_years,
                "action_on_fail": "reject_or_hold"
            })
            
        return {
            "hard_filters": rules,
            "soft_weights": {"default": "balanced"}
        }
