# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path
import shutil


from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from typing import Optional

from talentscope.io.salary import append_salary_to_csv
from talentscope.core.parser import CVParser
from talentscope.io.extractors import extract_resume_text
from talentscope.skills.skills_loader import load_yaml
import json

app = FastAPI(
    title="TalentScope API",
    description="API for TalentScope Engine: Job Matching & Candidate Ranking",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
JOBS_DIR = BASE_DIR / "jobs"
CV_DIR = DATA_DIR / "cv_pool"
SALARIES_CSV = DATA_DIR / "salaries.csv"
JSON_RESULTS_DIR = CV_DIR / "json_results"

JOBS_DIR.mkdir(parents=True, exist_ok=True)
CV_DIR.mkdir(parents=True, exist_ok=True, mode=0o755)
JSON_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/jobs/upload", summary="Upload a job description file")
async def upload_job_description(file: UploadFile = File(...)):
    """
    Uploads a job description file (.txt, .pdf, .docx) to the server.
    The file will be saved in the 'jobs' directory with a timestamp to avoid conflicts.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    path_obj = Path(filename)
    ext = path_obj.suffix.lower()
    
    allowed_extensions = {".txt", ".pdf", ".docx"}
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type '{ext}'. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Dosya ismine timestamp ekleyerek çakışmayı önleyelim
    stem = path_obj.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{stem}_{timestamp}{ext}"
    
    destination_path = JOBS_DIR / safe_filename

    try:
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save error: {str(e)}")

    return {
        "status": "success",
        "message": "File uploaded successfully",
        "original_filename": filename,
        "saved_filename": safe_filename,
        "file_path": str(destination_path)
    }


@app.post("/cv/upload", summary="Upload a CV, parse it, and return structured data")
async def upload_cv(
    file: UploadFile = File(...), 
    salary_expectation: Optional[str] = Form(None, description="Examples: '60000-70000', '80000', '50k'")
):
    """
    Uploads a CV file (.pdf, .docx), parses it immediately, and saves the structured JSON result.
    - Saves CV to 'talentscope/data/cv_pool'.
    - Saves Salary to 'talentscope/data/salaries.csv'.
    - Parses CV (IE) and saves JSON to 'talentscope/data/cv_pool/json_results'.
    - Returns the parsed data in the response.
    """
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is missing")
        
    path_obj = Path(filename)
    ext = path_obj.suffix.lower()
    allowed_extensions = {".pdf", ".docx"}
    
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type '{ext}'. Allowed types: {', '.join(allowed_extensions)}"
        )
        
    # 1. Save CV file
    destination_path = CV_DIR / filename
    
    try:
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File save error: {str(e)}")
        
    # 2. Handle Salary
    if salary_expectation:
        try:
            append_salary_to_csv(SALARIES_CSV, filename, salary_expectation)
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Salary save error: {str(e)}")

    # 3. Parse and Extract Data
    try:
        raw_text = extract_resume_text(str(destination_path))
        
        # Base Parsing
        parser = CVParser(raw_text)
        parsed_data = parser.parse()
        
        # Skill Extraction
        skills_path = Path("talentscope/skills/skills.yaml")
        if skills_path.exists():
            cfg = load_yaml(str(skills_path))
            from talentscope.core.normalize import norm
            norm_text = norm(raw_text)
            
            from talentscope.core.matcher import compile_patterns, score_text
            found_skills = set()
            
            domains = cfg.get("domains") or {}
            for dk, dv in domains.items():
                items = dv.get("items") or []
                if not items: continue
                
                compiled = compile_patterns(items)
                _, matched_list = score_text(norm_text, items, compiled)
                for canon, _, _ in matched_list:
                    found_skills.add(canon)
                    
            parsed_data["skills"] = sorted(list(found_skills))
            
        # Inject Salary
        parsed_data["salary"] = salary_expectation  # Use the input directly if available

        # 4. Save JSON Result
        json_filename = path_obj.stem + ".json"
        json_path = JSON_RESULTS_DIR / json_filename
        
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(parsed_data, jf, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "message": "CV uploaded and parsed successfully",
            "filename": filename,
            "parsed_data": parsed_data
        }

    except Exception as e:
         # Even if parsing fails, upload was successful
         # But usually we want to know parsing failed
         return {
             "status": "partial_success",
             "message": f"CV uploaded but parsing failed: {str(e)}",
             "filename": filename
         }


@app.get("/jobs", summary="List all uploaded job descriptions")
async def list_jobs():
    """
    Lists all job description files available in the 'jobs' directory.
    """
    if not JOBS_DIR.exists():
        return []

    files = []
    for f in JOBS_DIR.iterdir():
        if f.is_file() and f.name != ".gitkeep":
            stat = f.stat()
            files.append({
                "filename": f.name,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "path": str(f)
            })
    
    # Sort by creation time descending (newest first)
    files.sort(key=lambda x: x["created_at"], reverse=True)
    return files


from pydantic import BaseModel
from typing import Optional

class JobMatchRequest(BaseModel):
    job_filename: str
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    
@app.post("/jobs/match", summary="Find best candidates for a job with filters")
async def match_candidates(req: JobMatchRequest):
    """
    Finds the best matching CVs for a specific job description.
    Supports filtering by experience years and salary expectations.
    
    If no candidates match the strict filters, it returns the best candidates based on Job Fit Score (Fallback).
    """
    job_path = JOBS_DIR / req.job_filename
    if not job_path.exists():
        raise HTTPException(status_code=404, detail="Job file not found")
        
    skills_path = Path("talentscope/skills/skills.yaml") # Default location
    
    # Run the pipeline
    from talentscope.pipeline.pipeline import scan_pool
    
    try:
        # Scan all candidates first
        scan_result = scan_pool(
            cv_dir=str(CV_DIR),
            skills_yaml=str(skills_path),
            job_file=str(job_path),
            salaries_csv=str(SALARIES_CSV),
            min_fit_score=10.0, # Low threshold to get more candidates initially
            top_n=1000 
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine error: {str(e)}")
        
    all_candidates = scan_result.get("results", {}).get("salary_known_topN", []) + \
                     scan_result.get("results", {}).get("salary_unknown_topN", [])
                     
    filtered = []
    
    # Apply Filters
    for cand in all_candidates:
        valid = True
        
        # Experience Filter
        exp = cand.get("estimated_experience", 0)
        if req.min_experience is not None and exp < req.min_experience:
            valid = False
        if req.max_experience is not None and exp > req.max_experience:
            valid = False
            
        # Salary Filter
        # If candidate has no salary info, skip if strict salary filter is applied?
        # Or treat unknown as valid? Let's say valid if not strict, but here user asks for specific range.
        # Logic: If user sets limits, unknown salary is usually excluded or included?
        # Let's exclude unknown if filters are set.
        sal_mid = cand.get("salary_mid_tl")
        
        if (req.min_salary is not None or req.max_salary is not None):
            if sal_mid is None:
                valid = False
            else:
                if req.min_salary is not None and sal_mid < req.min_salary:
                    valid = False
                if req.max_salary is not None and sal_mid > req.max_salary:
                    valid = False
                    
        if valid:
            filtered.append(cand)
            
    is_fallback = False
    if not filtered:
        # Fallback: Return top candidates without filters
        filtered = all_candidates
        is_fallback = True
        
    # Sort Logic:
    # 1. HR Score (Desc)
    # 2. Job Fit Score (Desc)
    # 3. Experience (Desc)
    # 4. Salary (Asc)
    
    def sort_key(c):
        s_mid = c.get("salary_mid_tl") or float('inf')
        return (
            -c.get("hr_score", 0),
            -c["job_fit_score"],
            -c.get("estimated_experience", 0),
            s_mid
        )
    
    filtered.sort(key=sort_key)
    
    # HR Diversity Selection Logic (Top 10)
    # Target: 6 Safe, 2 Strong but Risky, 2 Potential
    
    final_selection = []
    if len(filtered) <= 10:
        final_selection = filtered
    else:
        # Categorize
        safe_bets = []
        risky_strong = [] # High score but maybe penalty or gap
        potentials = []   # Decent score but good school or pivot
        others = []
        
        for cand in filtered:
            score = cand.get("hr_score", 0)
            details = cand.get("hr_analysis", {})
            penalty = details.get("penalty", 0)
            school = details.get("school", 0)
            
            if score >= 70 and penalty == 0:
                safe_bets.append(cand)
            elif score >= 60 and penalty < 0:
                risky_strong.append(cand)
            elif score >= 50 and school > 0:
                potentials.append(cand)
            else:
                others.append(cand)
        
        # Select 6 Safe
        final_selection.extend(safe_bets[:6])
        
        # Select 2 Risky
        final_selection.extend(risky_strong[:2])
        
        # Select 2 Potential
        final_selection.extend(potentials[:2])
        
        # Fill remaining spots with best remaining from any category (sorted by score)
        needed = 10 - len(final_selection)
        if needed > 0:
            # Create pool of unselected
            selected_ids = {c["candidate_id"] for c in final_selection}
            remaining = [c for c in filtered if c["candidate_id"] not in selected_ids]
            final_selection.extend(remaining[:needed])
            
        # Re-sort final selection by score for display
        final_selection.sort(key=sort_key)

    top_10 = final_selection
    
    return {
        "status": "success",
        "fallback_triggered": is_fallback,
        "match_count": len(filtered),
        "hr_diversity_applied": len(filtered) > 10,
        "candidates": top_10
    }


@app.get("/cv/results", summary="List all parsed CV JSON results")
async def list_cv_results():
    """
    Lists all parsed CV data (JSON files) available in 'cv_pool/json_results'.
    """
    if not JSON_RESULTS_DIR.exists():
        return []

    files = []
    for f in JSON_RESULTS_DIR.iterdir():
        if f.is_file() and f.suffix.lower() == ".json":
            stat = f.stat()
            files.append({
                "filename": f.name,
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "path": str(f)
            })
    
    # Sort by creation time descending
    files.sort(key=lambda x: x["created_at"], reverse=True)
    return files


@app.get("/cv/results/{filename}", summary="Get parsed data for a specific CV")
async def get_cv_result(filename: str):
    """
    Returns the structured JSON data for a specific CV.
    Filename can be provided with or without .json extension.
    Example: 'candidate_cv.json' or 'candidate_cv'
    """
    if not filename.endswith(".json"):
        filename += ".json"
        
    file_path = JSON_RESULTS_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"CV result not found: {filename}")
        
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading JSON file: {str(e)}")






