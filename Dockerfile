# Main application image
FROM python:3.11-slim

LABEL maintainer="DFIR Community"
LABEL description="Automated malware capability analysis web service using capa"

# Install system dependencies including ClamAV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    clamav \
    clamav-daemon \
    clamav-freshclam \
    && rm -rf /var/lib/apt/lists/*

# Update ClamAV virus database
RUN freshclam || true

WORKDIR /app

# Copy capa rules (will be cloned during build or mounted)
RUN git clone --depth 1 https://github.com/mandiant/capa-rules.git /app/rules

# Install Python dependencies
COPY capa-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install capa
RUN pip install --no-cache-dir flare-capa

# Install badsign for YARA and ClamAV signature generation
COPY badsign/ /tmp/badsign/
RUN pip install --no-cache-dir /tmp/badsign && \
    rm -rf /tmp/badsign

# Copy application code
COPY capa-server/app/ /app/app/
COPY capa-server/static/ /app/static/

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/results && \
    chmod 777 /app/data/uploads /app/data/results

# Environment variables
ENV CAPA_RULES_PATH=/app/rules \
    DATABASE_PATH=/app/data/capa.db \
    UPLOAD_DIR=/app/data/uploads \
    RESULTS_DIR=/app/data/results \
    MAX_FILE_SIZE_MB=100 \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
