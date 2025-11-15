# capa-server Features Summary

Complete reference for all functionality available in capa-server and its standalone tools.

**Version:** 0.2.0
**Last Updated:** 2025-11-15

---

##  Core Features

### 1. Malware Capability Analysis

**What it does:** Automatically analyzes malware samples using capa to detect capabilities and behaviors

**How to use:**
- **Web UI:** Click "Upload to Server" button, select file
- **API:** `POST /api/analyze` with file upload
- **CLI:** Upload via curl or API client

**Supported formats:**
- Windows PE (.exe, .dll, .sys)
- Linux ELF binaries
- macOS Mach-O binaries
- .NET assemblies
- Raw shellcode (32-bit/64-bit)
- Sandbox reports (CAPE, VMRay, DRAKVUF)

**Documentation:** [README.md](README.md), [USAGE.md](USAGE.md)

---

### 2. ClamAV Pre-Scan

**What it does:** Automatically scans uploaded files with ClamAV antivirus before capa analysis

**How to use:** Automatic - runs on every upload

**Results include:**
- Scan status (clean/infected/error)
- Detected signature name (if infected)
- Scan timestamp
- Database version used

**API Response Fields:**
```json
{
  "clamav_scanned": true,
  "clamav_status": "infected",
  "clamav_signature": "Win.Trojan.Banker-123",
  "clamav_scan_time": "2025-11-15T10:30:00"
}
```

**Documentation:** [README.md](README.md#clamav-integration)

---

### 3. YARA Rule Generation

**What it does:** Generates behavioral YARA detection rules from capa analysis results

**How to use:**
- **Web UI:** Click " Generate YARA" button after analysis completes
- **API:** `GET /api/analyses/{id}/generate-yara`
- **CLI:** `badsign capa-to-yara analysis.json -o rule.yar`

**Parameters:**
- `rule_name` (optional) - Custom rule name
- `min_confidence` - Confidence level: low/medium/high (default: medium)
- `min_capabilities` - Minimum capabilities required (default: 2)

**Generated YARA includes:**
- Automatic malware categorization (Ransomware, Trojan, Backdoor, etc.)
- MITRE ATT&CK technique mapping
- API call and capability strings
- Cross-platform detection (PE/ELF/Mach-O)
- Confidence-based conditions

**Example:**
```bash
# Via API
curl "http://localhost:8080/api/analyses/1/generate-yara?min_confidence=high" -o malware.yar

# Standalone CLI
badsign capa-to-yara analysis.json -o malware.yar --min-confidence high --min-capabilities 3

# Test the rule
yara malware.yar /malware_samples/
```

**Documentation:** [BADSIGN_CLI.md](BADSIGN_CLI.md#2-capa-to-yara---generate-yara-from-capa-analysis)

---

### 4. ClamAV Signature Generation

**What it does:** Generates antivirus signatures for ClamAV from malware samples

**How to use:**
- **Web UI:** Click " Generate ClamAV" button after analysis completes
- **API:** `GET /api/analyses/{id}/generate-clamav`
- **CLI:** `badsign generate malware.exe -o signatures.ndb`

**Parameters:**
- `sig_name` (optional) - Custom signature name (defaults to filename)
- `include_strings` - Include string-based body signatures (default: true)
- `string_count` - Number of string signatures (default: 10)

**Generated signatures:**
1. **Hash signatures** - MD5 and SHA256 file hashes
2. **Body signatures** - Hex patterns from unique strings
3. **PE section hashes** - Section-specific signatures (PE files only)

**Output format:** Combined `.ndb` file with comments

**Extraction for ClamAV use:**
```bash
# Extract MD5 hashes (.hdb)
grep -E "^[0-9a-f]{32}:" signatures.ndb > malware.hdb

# Extract SHA256 hashes (.hsb)
grep -E "^[0-9a-f]{64}:" signatures.ndb > malware.hsb

# Extract body signatures (.ndb)
grep "^[A-Za-z].*:0:\*:" signatures.ndb > malware.ndb

# Extract PE section hashes (.mdb)
grep "^\." signatures.ndb > malware.mdb

# Test with ClamAV
clamscan -d malware.hdb suspicious_file.exe
```

**Documentation:**
- [README.md](README.md#using-generated-signatures)
- [BADSIGN_CLI.md](BADSIGN_CLI.md#1-generate---generate-all-signature-types)

---

### 5. Analysis Dashboard

**What it does:** Interactive web interface for viewing analysis results

**Features:**
- Recent analyses list with metadata
- File information (name, size, hash)
- ClamAV scan results
- Capability count
- MITRE ATT&CK techniques
- One-click signature generation
- Direct download of JSON results

**How to access:** Navigate to `http://localhost:8080/` in browser

**Documentation:** [README.md](README.md#web-interface-features)

---

### 6. capa Explorer Integration

**What it does:** Embedded capa Explorer Web UI for detailed capability analysis

**Features:**
- Interactive capability tree
- Search and filter capabilities
- MITRE ATT&CK mapping
- Detailed match information
- Export capabilities

**How to access:** Click on any completed analysis in the dashboard

**Documentation:** [capa Explorer Web](https://github.com/mandiant/capa/tree/master/web)

---

##  API Endpoints

### Analysis Management

| Endpoint | Method | Description | Documentation |
|----------|--------|-------------|---------------|
| `/api/analyze` | POST | Upload file for analysis | [README.md](README.md#post-apianalyze) |
| `/api/analyses` | GET | List all analyses | [README.md](README.md#get-apianalyses) |
| `/api/analyses/{id}` | GET | Get specific analysis | [README.md](README.md#get-apianalysesanalysis_id) |
| `/api/analyses/{id}` | DELETE | Delete analysis | [README.md](README.md#delete-apianalysesanalysis_id) |

### Export & Generation

| Endpoint | Method | Description | Documentation |
|----------|--------|-------------|---------------|
| `/api/analyses/{id}/download` | GET | Download JSON results | [README.md](README.md#get-apianalysesanalysis_iddownload) |
| `/api/analyses/{id}/generate-yara` | GET | Generate YARA rule | [README.md](README.md#get-apianalysesanalysis_idgenerate-yara) |
| `/api/analyses/{id}/generate-clamav` | GET | Generate ClamAV signatures | [README.md](README.md#get-apianalysesanalysis_idgenerate-clamav) |

### System

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/info` | GET | Server information and capabilities |
| `/docs` | GET | Interactive API documentation (Swagger UI) |

---

##  Standalone CLI Tools

### badsign

**Location:** `/home/robb/tools/badsign/`

**Installation:**
```bash
cd /home/robb/tools/badsign
pip install -e .
```

**Available Commands:**

| Command | Description | Example |
|---------|-------------|---------|
| `generate` | Generate all signature types | `badsign generate malware.exe -o sigs.ndb` |
| `capa-to-yara` | YARA from capa analysis | `badsign capa-to-yara analysis.json -o rule.yar` |
| `from-capa` | ClamAV from capa analysis | `badsign from-capa analysis.json -o sigs.ndb` |
| `hash` | Hash signatures only | `badsign hash malware.exe` |
| `extract` | Extract strings | `badsign extract malware.exe --min-entropy 4.5` |
| `validate` | Validate signatures | `badsign validate sigs.ndb --corpus /clean/files/` |

**Documentation:** [BADSIGN_CLI.md](BADSIGN_CLI.md)

**Python Library Usage:**
```python
from badsign import ClamAVSigGen
from badsign.yara_generator import YaraGenerator
from badsign.capa_parser import CapaParser

# Generate signatures
siggen = ClamAVSigGen(file_path="malware.exe")
signatures = siggen.generate_all(name="Malware")

# Generate YARA from capa
parser = CapaParser(capa_dict=analysis_data)
generator = YaraGenerator(parser)
yara_rule = generator.generate_rule()
```

---

##  Container Features

### Technology Stack

- **Base Image:** Debian 12 (Bookworm)
- **Python:** 3.11
- **Web Framework:** FastAPI with Uvicorn
- **Database:** SQLite with SQLAlchemy ORM
- **Analysis Engine:** capa (latest)
- **Antivirus:** ClamAV 1.4.3+ with virus database
- **Binary Parsing:** LIEF library

### Container Management

**Start container:**
```bash
podman-compose up -d    # or docker-compose up -d
```

**Stop container:**
```bash
podman-compose down     # or docker-compose down
```

**View logs:**
```bash
podman-compose logs -f  # or docker-compose logs -f
```

**Rebuild after changes:**
```bash
podman-compose down
podman-compose build
podman-compose up -d
```

**Reset database:**
```bash
podman-compose down
rm -rf ./data/*
podman-compose up -d
```

### Data Persistence

**Mounted volumes:**
- `./data/` - Database, uploaded files, analysis results
- `./rules/` - capa rules (optional custom rules)

**Data locations inside container:**
- `/app/data/capa.db` - SQLite database
- `/app/data/uploads/` - Uploaded malware samples
- `/app/data/results/` - Analysis JSON results
- `/app/rules/` - capa rules directory

---

##  Security Features

### Malware Handling

 **Pre-scan with ClamAV** - Automatic virus scanning before analysis
 **Isolated container** - Runs in Docker/Podman container
 **No network access required** - Offline analysis capability
 **File size limits** - Configurable maximum upload size (default: 100MB)

### Recommended Security Practices

- Run in isolated VM or network segment
- Do not expose to internet without authentication
- Use reverse proxy with authentication for multi-user access
- Regular ClamAV database updates (automatic in container)
- Monitor disk usage for uploaded samples
- Implement file retention policies

**Documentation:** [README.md](README.md#security-considerations)

---

##  Database Schema

### Analysis Table

Stores metadata and results for each analysis:

**Key Fields:**
- `id` - Unique analysis ID
- `filename` - Original filename
- `file_hash` - SHA256 hash
- `file_size` - File size in bytes
- `status` - pending/processing/completed/failed
- `clamav_scanned` - ClamAV scan performed (bool)
- `clamav_status` - clean/infected/error
- `clamav_signature` - Detected signature name
- `clamav_scan_time` - Scan timestamp
- `capa_version` - capa version used
- `capabilities_count` - Number of detected capabilities
- `attack_techniques` - MITRE ATT&CK techniques (JSON)
- `result_json` - Full capa results (JSON)
- `created_at` - Upload timestamp

**Schema Management:**

Adding new fields requires database reset:
```bash
podman-compose down
rm -rf ./data/*
podman-compose up -d
```

---

##  Complete Documentation Index

### User Guides
- [README.md](README.md) - Main documentation and feature overview
- [QUICKSTART.md](QUICKSTART.md) - 5-minute getting started guide
- [USAGE.md](USAGE.md) - Detailed usage instructions

### Signature Generation
- [BADSIGN_CLI.md](BADSIGN_CLI.md) - Complete CLI reference for standalone tools
- [SEPARATE_REPO_GUIDE.md](SEPARATE_REPO_GUIDE.md) - How to copy badsign to separate repository

### Development
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Architecture and design overview
- [NEXT_STEPS.md](NEXT_STEPS.md) - Development roadmap
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [FEATURES_SUMMARY.md](FEATURES_SUMMARY.md) - This document

### API Reference
- **Interactive Docs:** `http://localhost:8080/docs` (Swagger UI)
- **ReDoc:** `http://localhost:8080/redoc` (Alternative API docs)

---

##  Quick Reference

### Common Tasks

**Upload and analyze a file:**
```bash
curl -X POST -F "file=@malware.exe" http://localhost:8080/api/analyze
```

**Generate YARA rule:**
```bash
curl "http://localhost:8080/api/analyses/1/generate-yara" -o rule.yar
```

**Generate ClamAV signatures:**
```bash
curl "http://localhost:8080/api/analyses/1/generate-clamav" -o sigs.ndb
```

**Download JSON results:**
```bash
curl "http://localhost:8080/api/analyses/1/download" -o results.json
```

**List all analyses:**
```bash
curl http://localhost:8080/api/analyses
```

### Standalone CLI

**Generate YARA from capa analysis:**
```bash
capa malware.exe --json > analysis.json
badsign capa-to-yara analysis.json -o rule.yar
```

**Generate ClamAV signatures:**
```bash
badsign generate malware.exe --name "Malware" -o sigs.ndb
```

**Extract and test signatures:**
```bash
grep -E "^[0-9a-f]{32}:" sigs.ndb > malware.hdb
clamscan -d malware.hdb suspicious.exe
```

---

##  Support & Resources

### Getting Help

- **Documentation:** Check the guides listed above
- **API Docs:** `http://localhost:8080/docs`
- **Logs:** `podman-compose logs -f`
- **Health Check:** `curl http://localhost:8080/health`

### External Resources

- [capa Documentation](https://github.com/mandiant/capa)
- [ClamAV Signature Documentation](https://docs.clamav.net/manual/Signatures.html)
- [YARA Documentation](https://virustotal.github.io/yara/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Project Information

- **License:** Apache 2.0 (same as capa)
- **capa Version:** Latest (bundled in container)
- **Python Version:** 3.11+
- **Container Support:** Docker and Podman

---

**Last Updated:** 2025-11-15
**capa-server Version:** 0.2.0
**Generated by:** Claude Code (Anthropic)
