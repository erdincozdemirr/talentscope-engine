# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func
from talentscope.db.database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, unique=True, index=True)
    
    # Core Fields
    title = Column(String, nullable=True)
    job_family = Column(String, default="Software Engineering")
    job_track = Column(String, nullable=True) # e.g. Backend
    
    seniority_level = Column(String, nullable=True) # e.g. Senior
    min_xp = Column(Integer, nullable=True)
    max_xp = Column(Integer, nullable=True)
    
    education_level = Column(String, nullable=True) # e.g. bachelor
    military_required = Column(Boolean, default=False)
    work_model = Column(String, default="unspecified") # Remote/Hybrid
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Full JSON Backup
    full_json = Column(JSONB, nullable=True)

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, unique=True, index=True) # e.g. candidate_cv.pdf
    
    # Contact & Personal
    name = Column(String, nullable=True)
    email = Column(String, index=True, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    
    # Education (Most Relevant/Recent)
    school = Column(String, nullable=True)
    degree = Column(String, nullable=True)
    
    # Professional
    current_title = Column(String, nullable=True)
    current_company = Column(String, nullable=True)
    total_experience_years = Column(Float, default=0.0)
    salary_expectation = Column(String, nullable=True)
    
    # Skills Flattened
    skills = Column(ARRAY(String), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Full JSON Backup (No HR Score as requested)
    full_json = Column(JSONB, nullable=True)
