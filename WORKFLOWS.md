# capa-server Workflows

Complete workflows for building, running, and using capa-server.

---

## Table of Contents

1. [Building the Container](#1-building-the-container)
2. [Running the Container](#2-running-the-container)
3. [Analyzing Malware Samples](#3-analyzing-malware-samples)
4. [Cleanup](#4-cleanup)

---

## 1. Building the Container

### Prerequisites

- Docker or Podman installed
- Git installed
- ~500MB disk space for the container image

### Step-by-Step Build Process

#### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <repository-url> capa-server
cd capa-server
```

#### Step 2: Verify Files

```bash
# Check that key files exist
ls -l Dockerfile docker-compose.yml requirements.txt
ls -l app/ static/
```

Expected output should show:
- `Dockerfile` - Container build instructions
- `docker-compose.yml` - Orchestration configuration
- `requirements.txt` - Python dependencies
- `app/` - Backend application code
- `static/` - Frontend UI files

#### Step 3: Build the Container Image

**Using Docker Compose (Recommended):**

```bash
# Build the image
docker-compose build

# Or with Podman:
podman-compose build
```

**Using Docker directly:**

```bash
# Build the image
docker build -t capa-server:latest .

# Or with Podman:
podman build -t capa-server:latest .
```

**Build Process Details:**

The build will:
1. Pull Python 3.11 base image (~150MB)
2. Install system dependencies (git)
3. Clone capa-rules repository (~50MB, 1000+ detection rules)
4. Install Python dependencies (FastAPI, SQLAlchemy, etc.)
5. Install capa malware analysis framework
6. Copy application code and static files
7. Create data directories

**Expected build time:** 2-5 minutes (depending on internet speed)

**Verify the build:**

```bash
# Check that the image was created
docker images | grep capa-server

# Expected output:
# capa-server    latest    <image-id>    <time>    ~489 MB
```

---

## 2. Running the Container

### Option A: Using Docker Compose (Recommended)

Docker Compose handles all the configuration automatically.

#### Start the Container

```bash
# Start in detached mode
docker-compose up -d

# Or with Podman:
podman-compose up -d
```

#### Check Container Status

```bash
# View running containers
docker-compose ps

# Expected output:
# NAME          STATUS        PORTS
# capa-server   Up (healthy)  0.0.0.0:8080->8080/tcp
```

#### View Logs

```bash
# Follow logs in real-time
docker-compose logs -f

# View last 50 lines
docker-compose logs --tail 50

# Check for successful startup - should see:
# INFO:     Started server process [1]
# INFO:     Uvicorn running on http://0.0.0.0:8080
# INFO:     Found 1019 rule files in /app/rules
```

### Option B: Using Docker/Podman Directly

#### Run with Docker

```bash
docker run -d \
  --name capa-server \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data:Z \
  --restart unless-stopped \
  capa-server:latest
```

#### Run with Podman

```bash
podman run -d \
  --name capa-server \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data:Z \
  --restart unless-stopped \
  capa-server:latest
```

**Important Options Explained:**

- `-d` - Run in detached (background) mode
- `--name capa-server` - Name the container
- `-p 8080:8080` - Map port 8080 (host:container)
- `-v $(pwd)/data:/app/data:Z` - Persist database and uploads
  - `:Z` flag is important for SELinux/Podman rootless environments
- `--restart unless-stopped` - Auto-restart on system reboot

### Verify the Container is Running

```bash
# Test the health endpoint
curl http://localhost:8080/health

# Expected output:
# {"status":"healthy","version":"0.1.0"}
```

```bash
# Check server info
curl http://localhost:8080/api/info

# Expected output:
# {
#   "name": "capa-server",
#   "version": "0.1.0",
#   "capa_rules_count": 1019,
#   "max_file_size_mb": 100
# }
```

### Access the Web Interface

Open your browser and navigate to:

- **Main UI:** http://localhost:8080
- **Explorer UI:** http://localhost:8080/explorer
- **API Documentation:** http://localhost:8080/docs

---

## 3. Analyzing Malware Samples

### Method A: Web Interface (Easiest)

#### Step 1: Access the Upload Interface

Open http://localhost:8080 in your browser.

#### Step 2: Upload a Sample

1. **Drag and drop** a malware sample onto the upload area
   - OR -
2. **Click the upload area** to browse for a file

**Supported file types:**
- PE executables (.exe, .dll, .sys)
- ELF binaries
- .NET assemblies
- Shellcode
- Sandbox reports (JSON)

**File size limit:** 100MB (configurable in docker-compose.yml)

#### Step 3: Monitor Analysis Progress

The "Recent Analyses" section will show:
- **pending** - Queued for analysis
- **processing** - Currently analyzing
- **completed** - Analysis finished successfully
- **failed** - Analysis encountered an error

**Note:** Analysis time varies:
- Small files (< 100KB): 10-30 seconds
- Medium files (100KB - 1MB): 30-60 seconds
- Large files (> 1MB): 1-5 minutes

#### Step 4: View Results

When status shows **completed**:

1. **Click "View Results"** - Opens the capa Explorer with analysis data
   - The Explorer automatically loads the JSON results
   - Browse capabilities, ATT&CK techniques, and detailed matches

2. **Click "Download JSON"** - Download raw analysis results
   - Standard capa JSON format
   - Can be used with other tools or re-imported later

### Method B: Command Line Interface

#### Using cURL

```bash
# Upload a sample
curl -X POST \
  -F "file=@/path/to/malware.exe" \
  http://localhost:8080/api/analyze

# Response:
# {
#   "message": "Analysis started",
#   "analysis_id": 1,
#   "duplicate": false
# }
```

```bash
# Check analysis status
ANALYSIS_ID=1
curl http://localhost:8080/api/analyses/$ANALYSIS_ID

# Response includes:
# {
#   "id": 1,
#   "filename": "malware.exe",
#   "status": "completed",
#   "capabilities_count": 42,
#   "attack_techniques": ["T1055", "T1082", ...],
#   ...
# }
```

```bash
# Download results
curl http://localhost:8080/api/analyses/$ANALYSIS_ID/download \
  -o analysis-results.json
```

#### Using the Test Script

The repository includes a test script for automated testing:

```bash
# Run basic tests
./test-api.sh

# Test with a specific file
TEST_FILE=/path/to/malware.exe ./test-api.sh
```

### Method C: Programmatic Access (Python)

```python
import requests
import time

# Configuration
API_BASE = "http://localhost:8080"

# Upload file
with open("/path/to/malware.exe", "rb") as f:
    response = requests.post(
        f"{API_BASE}/api/analyze",
        files={"file": f}
    )
    data = response.json()
    analysis_id = data["analysis_id"]
    print(f"Analysis started: ID {analysis_id}")

# Poll for completion
while True:
    response = requests.get(f"{API_BASE}/api/analyses/{analysis_id}")
    analysis = response.json()
    status = analysis["status"]

    print(f"Status: {status}")

    if status == "completed":
        print(f"Found {analysis['capabilities_count']} capabilities")
        print(f"ATT&CK techniques: {analysis['attack_techniques']}")
        break
    elif status == "failed":
        print(f"Error: {analysis['error_message']}")
        break

    time.sleep(2)

# Download full results
response = requests.get(f"{API_BASE}/api/analyses/{analysis_id}")
results = response.json()["results"]

# Save to file
import json
with open(f"analysis-{analysis_id}.json", "w") as f:
    json.dump(results, f, indent=2)
```

### Understanding Analysis Results

#### Capabilities

capa identifies capabilities in the following categories:

- **Anti-Analysis** - Debugger detection, VM detection, sandbox evasion
- **Collection** - Keylogging, screen capture, clipboard access
- **Communication** - HTTP requests, DNS queries, IRC, email
- **Data Manipulation** - Encryption, compression, encoding
- **Execution** - Code injection, DLL loading, thread manipulation
- **File System** - File operations, registry access
- **Host Interaction** - Service manipulation, process enumeration
- **Persistence** - Registry run keys, scheduled tasks, DLL hijacking

#### ATT&CK Mapping

Each capability is mapped to MITRE ATT&CK techniques:

- **Example:** `T1055` = Process Injection
- **Example:** `T1082` = System Information Discovery
- **Example:** `T1027` = Obfuscated Files or Information

#### Result Confidence

- **High confidence:** Multiple matching rules with strong evidence
- **Medium confidence:** Fewer matches or less specific indicators
- **Low confidence:** Weak indicators or generic patterns

---

## 4. Cleanup

### Stop the Container

```bash
# Using Docker Compose
docker-compose down

# Or using Docker directly
docker stop capa-server
docker rm capa-server
```

### Remove the Image

```bash
# Using Docker
docker rmi capa-server:latest

# Or using Podman
podman rmi capa-server:latest
```

### Clean Up Data (Optional)

** Warning:** This will delete all analysis results and the database!

```bash
# Remove persisted data
rm -rf data/

# Or clean but preserve directory structure
rm -f data/capa.db
rm -rf data/uploads/* data/results/*
```

### Complete Cleanup

```bash
# Stop and remove everything
docker-compose down
docker rmi capa-server:latest
rm -rf data/

# Or with Podman
podman-compose down
podman rmi capa-server:latest
rm -rf data/
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs

# Common issues:
# - Port 8080 already in use: Change port in docker-compose.yml
# - Permission issues: Check data directory permissions
# - Disk space: Ensure adequate space for rules and uploads
```

### Analysis Fails

```bash
# Check container logs
docker-compose logs | grep ERROR

# Common issues:
# - Unsupported file format: capa only supports PE/ELF/.NET
# - File too large: Increase MAX_FILE_SIZE_MB in docker-compose.yml
# - Corrupted file: Verify file integrity
```

### Can't Access Web Interface

```bash
# Verify container is running
docker-compose ps

# Test health endpoint
curl http://localhost:8080/health

# Check firewall rules
sudo firewall-cmd --list-ports
```

### Performance Issues

```bash
# Increase resource limits in docker-compose.yml
services:
  capa-server:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

---

## Advanced Configuration

### Custom Rules Path

```yaml
# docker-compose.yml
services:
  capa-server:
    volumes:
      - ./custom-rules:/app/custom-rules:Z
    environment:
      - CAPA_RULES_PATH=/app/custom-rules
```

### Increase File Size Limit

```yaml
# docker-compose.yml
services:
  capa-server:
    environment:
      - MAX_FILE_SIZE_MB=500  # Default: 100
```

### Enable Debug Logging

```yaml
# docker-compose.yml
services:
  capa-server:
    environment:
      - DEBUG=true
```

### Change Port

```yaml
# docker-compose.yml
services:
  capa-server:
    ports:
      - "9000:8080"  # Access via http://localhost:9000
```

---

## Quick Reference

### One-Line Commands

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down

# Check status
curl http://localhost:8080/health

# Analyze file
curl -F "file=@sample.exe" http://localhost:8080/api/analyze

# List analyses
curl http://localhost:8080/api/analyses
```

---

## Next Steps

- Review [USAGE.md](USAGE.md) for detailed API documentation
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Check [NEXT_STEPS.md](NEXT_STEPS.md) for enhancement ideas
- Report issues or contribute at [GitHub repository]

---

**Need Help?**

- Check logs: `docker-compose logs -f`
- Test API: Visit http://localhost:8080/docs
- View health: `curl http://localhost:8080/health`
