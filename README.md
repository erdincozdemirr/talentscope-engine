# TalentScope Engine v2

**TalentScope** is a next-generation **HR Tech Engine** designed to automate the recruitment screening process with explainable, rule-based logic.

Unlike traditional keyword scanners, TalentScope acts as a transparent **Decision Support System** for HR teams. It ingests CVs and Job Descriptions, parses them into structured data, applies complex "Turkish HR Practice" scoring rules, and provides a diversity-focused shortlist of candidates.

---

## 🏗 System Architecture

The system follows a **Microservices-ready** architecture, leveraging a polyglot persistence layer to handle different types of data efficiently.

```mermaid
graph TD
    User[Recruiter / System] -->|Upload PDF/DOCX| API[FastAPI Engine]
    
    subgraph "Data Processing Pipeline"
        API -->|1. Parse & Extract| Parser[IE Engine]
        API -->|2. Store File| MinIO[MinIO Object Storage]
        API -->|3. Save Metadata| DB[(PostgreSQL)]
    end
    
    subgraph "Matching Engine"
        API -->|4. Request Match| Matcher[HR Scorer & Ranker]
        Matcher -->|Fetch Candidates| DB
        Matcher -->|Calculate Score| Metrics[HR Metrics]
        Matcher -->|Log Result| Mongo[(MongoDB)]
    end
    
    Matcher -->|5. Return Top 10| User
```

---

## 🚀 Key Features

### 1. Intelligent Document Parsing (IE)
TalentScope converts unstructured documents into rich, structured JSON data without relying on black-box AI models.
*   **CV Parsing:** Extracts Contact Info, Experience (Years, Titles), Education (Degree, School), and Skills.
*   **Job Parsing:** Automatically detects Seniority Level (Junior/Mid/Senior), Required Tech Stack (Backend, DevOps, etc.), and Eligibility rules (Military, Hybrid/Remote).

### 2. Advanced HR Scoring Engine
Candidates are not just matched by keywords. They are evaluated on a **6-Dimensional HR Matrix** (0-100 Score):
*   **Operational Fit (25%):** Checks Military Status (Completed/Exempt), Salary Expectations vs. Budget, and Commute/Location.
*   **Role & Level Fit (25%):** Matches Candidate's Experience Years and Current Title against the Job Description.
*   **Evidence Verification (20%):** Cross-references "Listed Skills" with "Experience Descriptions" to find proof of usage (e.g., *Used Java in Project X*).
*   **Experience Quality (15%):** Heuristic analysis of the CV's professional language and detail level.
*   **Stability (10%):** Detects "Job Hopping" patterns (frequent job changes in short periods).
*   **University & Pivot (5%):** Bonus points for Tier-1 Universities or successful career pivots.

### 3. Diversity-First Matching Algorithm
The matching engine does not simply return the top 10 highest scorers. It curates a **Strategic Shortlist** to give HR a variety of options:
*   🟢 **6 Safe Bets:** High Score, Low Risk. The "Ideal" candidates.
*   🔴 **2 Risky but Strong:** Excellent technical fit but may have minor risks (e.g., high salary, location).
*   🟡 **2 High Potential:** Lower experience but strong educational background or high growth potential.

### 4. Polyglot Data Persistence
*   **PostgreSQL:** Stores structured, queryable metadata (Experience Years, Skills Array, Contact Info) in a **Column-Heavy** schema for fast filtering.
*   **MongoDB:** Logs every single match result (`Job ID` <-> `Candidate ID`) as a document for analytics and audit trails.
*   **MinIO (S3):** securely stores the original raw PDF/DOCX files.

---

## 🛠 Tech Stack

*   **Language:** Python 3.11
*   **Framework:** FastAPI (High-performance Async API)
*   **Databases:**
    *   **PostgreSQL 15** (Relational Data)
    *   **MongoDB 6.0** (Match Logs)
*   **Storage:** MinIO (Object Storage)
*   **DevOps:** Docker & Docker Compose
*   **Transformation:** SQLAlchemy, PyMongo, PDFMiner

---

## 🐳 Getting Started (Docker - Recommended)

The easiest way to run TalentScope is using Docker Compose. This will orchestrate the API and all dependencies.

### Prerequisites
*   Docker & Docker Compose installed on your machine.

### Installation Steps

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-org/talentscope-engine.git
    cd talentscope-engine
    ```

2.  **Start the Services**
    ```bash
    docker-compose up --build -d
    ```
    *This starts Postgres (5432), Mongo (27017), MinIO (9000/9001), and the TalentScope API (8000).*

3.  **Verify Installation**
    *   **Swagger UI:** Open [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **MinIO Console:** Open [http://localhost:9001](http://localhost:9001)
        *   User: `minioadmin`
        *   Pass: `minioadmin`

---

## 🐢 Getting Started (Local Development)

If you prefer running the Python application locally (e.g., for debugging), follow these steps.

1.  **Set up Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variables**
    Ensure you have the databases running (e.g., via Docker or locally). Then export the configs:
    ```bash
    export DATABASE_URL="postgresql://user:password@localhost:5432/talentscope"
    export MONGO_URI="mongodb://localhost:27017/"
    export MINIO_ENDPOINT="localhost:9000"
    export MINIO_ACCESS_KEY="minioadmin"
    export MINIO_SECRET_KEY="minioadmin"
    ```

4.  **Run the Server**
    ```bash
    python3 -m uvicorn talentscope.api:app --reload
    ```

---

## � Service Access & Credentials (Docker Defaults)

When running via `docker-compose`, the services are pre-configured with the following credentials.

| Service | Port (Host) | URL / Connection String | Username | Password | Database / Bucket |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **API (Swagger)** | `8000` | [http://localhost:8000/docs](http://localhost:8000/docs) | - | - | - |
| **MinIO Console** | `9001` | [http://localhost:9001](http://localhost:9001) | `minioadmin` | `minioadmin` | `cvs`, `jobs` |
| **MinIO API** | `9000` | `http://localhost:9000` | `minioadmin` | `minioadmin` | - |
| **PostgreSQL** | `5432` | `postgresql://user:password@localhost:5432/talentscope` | `user` | `password` | `talentscope` |
| **MongoDB** | `27017` | `mongodb://localhost:27017/` | - | - | `talentscope_matches` |

---

## �📡 API Usage Guide

### 1. Upload a Job Description
**Endpoint:** `POST /jobs/upload`
*   **Input:** PDF, DOCX, or TXT file.
*   **Process:** Parses seniority, tech stack, and benefits. Saves to MinIO and Postgres.
*   **Output:** JSON structure of the job requirements.

### 2. Upload a Candidate CV
**Endpoint:** `POST /cv/upload`
*   **Input:** PDF/DOCX file + `salary_expectation` (Form Field).
*   **Process:** Parses skills, experience, and contact info. Estimates experience years. Saves to MinIO and Postgres.
*   **Output:** JSON structure of the candidate profile.

### 3. Match & Rank Candidates
**Endpoint:** `POST /jobs/match`
*   **Input:**
    *   `job_filename`: The ID of the uploaded job (e.g., `backend_dev_2023.pdf`).
    *   (Optional) Filters: `min_experience`, `max_experience`, `min_salary`, etc.
*   **Process:** Scans the candidate pool, scores them against the job, applies diversity logic, and logs results to MongoDB.
*   **Output:** Top 10 Candidates with detailed score breakdowns.

---

## ⚙️ Configuration

All configurations are centralized in `talentscope/config.py`. You can override them using Environment Variables.

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://...@localhost...` | PostgreSQL Connection String |
| `MONGO_URI` | `mongodb://localhost:27017/` | MongoDB Connection URI |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO API Address |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO Access Key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO Secret Key |
| `MINIO_SECURE` | `False` | Set `True` for HTTPS |

---

## � Project Structure

```
talentscope-engine/
├── docker-compose.yml       # Service Orchestration
├── Dockerfile              # API Image Definition
├── requirements.txt        # Python Dependencies
├── README.md               # Documentation
└── talentscope/
    ├── api.py              # Main FastAPI Application
    ├── config.py           # Configuration Management
    ├── core/               # Business Logic
    │   ├── job_parser.py   # Job Description Analysis
    │   ├── parser.py       # Resume Analysis (IE)
    │   ├── hr_scorer.py    # Scoring Algorithm
    │   └── hr_metrics.py   # Metric Calculators
    ├── db/                 # Database Layer
    │   ├── database.py     # Postgres Session & Init
    │   ├── models.py       # SQL Models (Jobs, Candidates)
    │   └── mongo_client.py # Mongo Wrapper
    ├── io/                 # Input/Output Layer
    │   ├── minio_client.py # Object Storage Wrapper
    │   └── extractors.py   # File Text Extraction
    └── skills/             # Knowledge Base
        └── skills.yaml     # Skill Definitions & Taxonomy
```