# Base Image
FROM python:3.11-slim

# System Dependencies
# libpq-dev: for psycopg2
# poppler-utils: for pdfminer/text extraction if needed
# build-essential: for compiling some python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    poppler-utils \
    git \
    && rm -rf /var/lib/apt/lists/*

# Work Directory
WORKDIR /app

# Copy Requirements
COPY requirements.txt .

# Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
# We copy the 'talentscope' package into /app/talentscope
COPY talentscope ./talentscope

# Create necessary directories for mounting volumes (to avoid permission issues)
RUN mkdir -p /app/data /app/jobs /app/cv_pool

# Expose API Port
EXPOSE 8000

# Run Application
CMD ["uvicorn", "talentscope.api:app", "--host", "0.0.0.0", "--port", "8000"]
