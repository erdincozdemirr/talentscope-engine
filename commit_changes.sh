#!/bin/bash

# Add all changes
git add .

# Commit with a detailed message
git commit -m "feat: TalentScope v2.0 - Full Stack HR Engine

Major release transforming the engine into a full-stack microservices-ready system.

Key Features:
- feat(ie): Added 'JobParser' for structured JD analysis (Seniority, Tech Stack, Evidence).
- feat(db): Integrated PostgreSQL for Column-Heavy metadata storage (Jobs & Candidates).
- feat(db): Integrated MongoDB for logging Match Results (Job-Candidate pairs).
- feat(storage): Added MinIO (S3) integration for file persistence.
- feat(infra): Dockerized the entire stack (API, Postgres, Mongo, MinIO) with docker-compose.
- refactor(config): Centralized configuration in 'talentscope/config.py'.
- docs: Rewrote README.md with architecture diagrams and detailed usage guide.
"

echo "Changes committed successfully."
