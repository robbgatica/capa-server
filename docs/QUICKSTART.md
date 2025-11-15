# capa-server Quick Start

Get up and running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- 1GB free disk space
- Port 8080 available

## Installation

```bash
cd ~/tools/capa-server

# Start the service
docker-compose up -d

# Watch it start
docker-compose logs -f
```

Wait for: `Application startup complete`

## Access

Open your browser: **http://localhost:8080**

## Upload Your First Sample

1. Drag and drop a PE/ELF file onto the upload area
2. Watch the "Recent Analyses" section for status
3. When status changes to "completed", click "View Results"
4. Download JSON for use in capa Explorer Web

## Test with Sample Data

```bash
# Download a test sample (benign calc.exe)
curl -L https://github.com/mandiant/capa/raw/master/tests/data/Practical%20Malware%20Analysis%20Lab%2001-01.dll_ -o test.dll

# Upload it
curl -X POST -F "file=@test.dll" http://localhost:8080/api/analyze

# Check results
./test-api.sh
```

## Troubleshooting

**Container won't start?**
```bash
docker-compose down
docker-compose up --build
```

**Port 8080 in use?**
```yaml
# Edit docker-compose.yml
ports:
  - "9000:8080"  # Use port 9000 instead
```

**Analysis fails?**
- Check file is a valid PE/ELF/shellcode
- Check logs: `docker-compose logs -f`
- File might be too large (default limit: 100MB)

## Next Steps

- Read [USAGE.md](USAGE.md) for API details
- Read [NEXT_STEPS.md](NEXT_STEPS.md) for development info
- Check [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for architecture overview

## Stop the Service

```bash
docker-compose down

# Remove data too
docker-compose down -v
```

---

That's it! You're running capa as a service.
