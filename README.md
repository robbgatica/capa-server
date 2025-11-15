# capa-server

> **Automated malware capability analysis as a service**

A containerized web service for automated malware capability analysis using [capa](https://github.com/mandiant/capa).

![Status](https://img.shields.io/badge/status-alpha-orange)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Docker](https://img.shields.io/badge/container-Docker%20%7C%20Podman-blue)

**[Quick Start](QUICKSTART.md)** | **[Usage Guide](USAGE.md)** | **[API Docs](http://localhost:8080/docs)** | **[Contributing](CONTRIBUTING.md)**

## Features

- **Web UI**: Upload binaries and view analysis results through the integrated capa Explorer Web interface
- **REST API**: Programmatic access for automation and CI/CD integration
- **Automated Analysis**: Automatic capa analysis on file upload
- **ClamAV Pre-Scan**: Automatic virus scanning before analysis with result tracking
- **YARA Rule Generation**: Create behavioral YARA rules from capa analysis results
- **ClamAV Signature Generation**: Generate hash, body, and PE section signatures from malware samples
- **Persistent Storage**: SQLite database for analysis history and results
- **Multi-Format Support**: PE, ELF, .NET, shellcode, and sandbox reports (CAPE, VMRay, DRAKVUF)
- **JSON Export**: Download results in capa's JSON format for further processing

## Quick Start

### Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Using Podman Compose (Fedora/RHEL)

```bash
podman-compose up -d
```

Access the web interface at `http://localhost:8080`

### Manual Container Run

Works with both Docker and Podman:

```bash
# Docker
docker build -t capa-server .
docker run -p 8080:8080 -v $(pwd)/data:/app/data capa-server

# Podman (rootless)
podman build -t capa-server .
podman run -p 8080:8080 -v $(pwd)/data:/app/data:Z capa-server
```

Note: Podman on SELinux systems (Fedora/RHEL) needs the `:Z` flag for volume mounts.

See [PODMAN.md](PODMAN.md) for detailed Podman instructions.

## Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: capa Explorer Web (Vue.js 3)
- **Analysis Engine**: capa with bundled rules
- **Antivirus Scanner**: ClamAV 1.4.3+ with automatic database updates
- **Signature Generator**: badsign (YARA and ClamAV signature generation)
- **Database**: SQLite with SQLAlchemy ORM
- **Web Server**: Uvicorn (ASGI)
- **Container**: Docker/Podman with Debian base

## API Endpoints

### POST /api/analyze
Upload a binary for analysis (includes automatic ClamAV pre-scan)

```bash
curl -X POST -F "file=@malware.exe" http://localhost:8080/api/analyze
```

**Response:**
```json
{
  "message": "Analysis started",
  "analysis_id": 1,
  "duplicate": false
}
```

### GET /api/analyses
List all analyses with ClamAV scan results

```bash
curl http://localhost:8080/api/analyses
```

### GET /api/analyses/{analysis_id}
Get specific analysis result including ClamAV scan data

```bash
curl http://localhost:8080/api/analyses/{id}
```

**Response includes:**
- `clamav_scanned`: Whether ClamAV scan was performed
- `clamav_status`: Scan result (clean, infected, error)
- `clamav_signature`: Detected signature name (if infected)
- `clamav_scan_time`: When scan was performed

### GET /api/analyses/{analysis_id}/download
Download analysis JSON

```bash
curl http://localhost:8080/api/analyses/{id}/download -o results.json
```

### GET /api/analyses/{analysis_id}/generate-yara
Generate YARA rule from capa analysis results

```bash
# Basic usage
curl "http://localhost:8080/api/analyses/{id}/generate-yara" -o rule.yar

# With parameters
curl "http://localhost:8080/api/analyses/{id}/generate-yara?min_confidence=medium&min_capabilities=2&rule_name=MyMalware" -o rule.yar
```

**Parameters:**
- `rule_name` (optional): Custom rule name (auto-generated from capabilities if not provided)
- `min_confidence`: Minimum confidence level - `low`, `medium`, or `high` (default: `medium`)
- `min_capabilities`: Minimum number of capabilities required (default: `2`)

**Returns:** Downloadable `.yar` YARA rule file

### GET /api/analyses/{analysis_id}/generate-clamav
Generate ClamAV signatures from malware sample

```bash
# Basic usage
curl "http://localhost:8080/api/analyses/{id}/generate-clamav" -o signatures.ndb

# With parameters
curl "http://localhost:8080/api/analyses/{id}/generate-clamav?include_strings=true&string_count=10&sig_name=MyMalware" -o signatures.ndb
```

**Parameters:**
- `sig_name` (optional): Custom signature name (defaults to filename)
- `include_strings`: Include string-based body signatures (default: `true`)
- `string_count`: Number of string signatures to generate (default: `10`)

**Returns:** Downloadable `.ndb` file containing:
- Hash signatures (MD5 and SHA256)
- Body signatures (hex patterns from unique strings)
- PE section hash signatures (if PE file)

**Note:** The `.ndb` file contains multiple signature types with comments. Extract specific types for ClamAV use:

```bash
# Extract MD5 hash signatures (.hdb)
grep -E "^[0-9a-f]{32}:" signatures.ndb > malware.hdb

# Extract SHA256 signatures (.hsb)
grep -E "^[0-9a-f]{64}:" signatures.ndb > malware.hsb

# Extract body signatures (.ndb)
grep "^[A-Za-z].*:0:\*:" signatures.ndb > malware.ndb

# Extract PE section hashes (.mdb)
grep "^\." signatures.ndb > malware.mdb
```

### DELETE /api/analyses/{analysis_id}
Delete an analysis and its files

```bash
curl -X DELETE http://localhost:8080/api/analyses/{id}
```

## Web Interface Features

### Upload and Analysis
1. **Upload Files**: Click "Upload to Server" button on the home page
2. **Automatic Processing**:
   - ClamAV scans the file first
   - capa analysis runs automatically
   - Results appear in the dashboard when complete

### Analysis Dashboard
- View recent analyses with metadata
- See ClamAV scan results (clean/infected/error)
- Click any analysis to view detailed capability results
- Access MITRE ATT&CK techniques mapped to behaviors

### Generate Signatures
For each completed analysis, you can:

**Download JSON** - Get the full capa analysis results
```
 Download JSON
```

**Generate YARA Rule** - Create behavioral detection rule
```
 Generate YARA
```
- Automatically categorizes malware (Ransomware, Trojan, Backdoor, etc.)
- Includes MITRE ATT&CK techniques
- Configurable confidence levels
- Ready to use with YARA scanner

**Generate ClamAV Signatures** - Create antivirus signatures
```
 Generate ClamAV
```
- Hash-based signatures (MD5, SHA256)
- String-based body signatures
- PE section hashes
- Extract and use with ClamAV

## ClamAV Integration

### Automatic Pre-Scanning

Every uploaded file is automatically scanned with ClamAV before capa analysis:

1. **File Upload** → ClamAV scan → capa analysis → Results
2. Scan results are stored in the database
3. Detection signatures are tracked and displayed

### Using Generated Signatures

The generated `.ndb` file contains multiple signature types with documentation comments. To use with ClamAV:

```bash
# Download signatures from capa-server
curl "http://localhost:8080/api/analyses/1/generate-clamav" -o sigs.ndb

# Extract specific signature types
grep -E "^[0-9a-f]{32}:" sigs.ndb > malware.hdb    # MD5 hashes
grep -E "^[0-9a-f]{64}:" sigs.ndb > malware.hsb    # SHA256 hashes
grep "^[A-Za-z].*:0:\*:" sigs.ndb > malware.ndb    # Body signatures
grep "^\." sigs.ndb > malware.mdb                  # PE sections

# Use with ClamAV
clamscan -d malware.hdb suspicious_file.exe
clamscan -d malware.ndb suspicious_file.exe

# Add to ClamAV database (requires root)
sudo cp malware.hdb /var/lib/clamav/
sudo systemctl reload clamav-daemon
```

### Database Management

If you change the database schema (e.g., adding new fields), you'll need to reset the database:

```bash
# Stop containers
podman-compose down  # or docker-compose down

# Remove old database
rm -rf ./data/*

# Restart (database will be recreated)
podman-compose up -d  # or docker-compose up -d
```

## Configuration

Environment variables:

- `CAPA_RULES_PATH`: Path to capa rules directory (default: `/app/rules`)
- `DATABASE_PATH`: SQLite database path (default: `/app/data/capa.db`)
- `UPLOAD_DIR`: Binary storage directory (default: `/app/data/uploads`)
- `MAX_FILE_SIZE`: Maximum upload size in MB (default: 100)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Security Considerations

This is designed for **internal lab use** or **isolated analysis environments**:

- No authentication by default (add reverse proxy with auth for production)
- Handles malware samples (run in isolated network/VM)
- File uploads are stored on disk (ensure proper storage limits)
- Consider running with read-only filesystem mounts where possible

## Project Status

**Current**: Alpha - Core functionality working, needs production hardening

**Ready to use for**:
- Local lab environments
- Learning and experimentation
- Internal team testing

**Not yet ready for**:
- Production deployment
- Internet-facing services
- Multi-user environments

See [NEXT_STEPS.md](NEXT_STEPS.md) for the roadmap.

## Standalone CLI Tools

The signature generation functionality is available as standalone CLI tools:

### badsign

Generate YARA rules and ClamAV signatures independently of the server:

```bash
# Generate YARA rule from capa analysis
badsign capa-to-yara analysis.json -o rule.yar

# Generate ClamAV signatures from binary
badsign generate malware.exe --name "Malware" -o sigs.ndb
```

**See [BADSIGN_CLI.md](BADSIGN_CLI.md)** for complete CLI documentation and standalone usage guide.

**Repository Location:** `/home/robb/tools/badsign/`

**Want to use this separately?** See [SEPARATE_REPO_GUIDE.md](SEPARATE_REPO_GUIDE.md) for instructions on copying badsign to its own repository.

## Documentation

 **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Complete navigation guide to all documentation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[USAGE.md](USAGE.md)** - Detailed usage guide
- **[FEATURES_SUMMARY.md](FEATURES_SUMMARY.md)** - Complete feature reference

### Signature Generation
- **[BADSIGN_CLI.md](BADSIGN_CLI.md)** - Standalone CLI tools reference and complete command documentation
- **[SEPARATE_REPO_GUIDE.md](SEPARATE_REPO_GUIDE.md)** - How to copy badsign to a separate repository

### Maintenance
- **[MAINTENANCE.md](MAINTENANCE.md)** - Repository cleanup, updates, and database migration

### Development
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Architecture and design
- **[NEXT_STEPS.md](NEXT_STEPS.md)** - Development roadmap
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute

## Contributing

Contributions welcome! This is an independent project built on top of capa.

For capa itself, see https://github.com/mandiant/capa

## Acknowledgments

Built with:
- [capa](https://github.com/mandiant/capa) by Mandiant FLARE team
- [FastAPI](https://fastapi.tiangolo.com) web framework
- [SQLAlchemy](https://www.sqlalchemy.org) ORM

## License

Apache 2.0 (matching capa's license) - See [LICENSE](LICENSE)
