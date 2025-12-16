# -*- coding: utf-8 -*-
import os

class MinioConfig:
    ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"
    
    # Bucket Names
    BUCKET_JOBS = "jobs"
    BUCKET_CVS = "cvs"

class SwaggerConfig:
    TITLE = "TalentScope API"
    DESCRIPTION = "API for TalentScope Engine: Job Matching & Candidate Ranking"
    VERSION = "1.0.0"

class DBConfig:
    URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/talentscope")

class MongoConfig:
    URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("MONGO_DB_NAME", "talentscope_matches")
    COLLECTION_MATCHES = "job_matches"


