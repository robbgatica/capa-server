# capa-server Usage Guide

## Quick Start

### 1. Start the server

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or using Make
make up
```

### 2. Access the web interface

Open your browser to: `http://localhost:8080`

### 3. Upload a binary

- Drag and drop a file onto the upload area, or
- Click the upload area to browse for a file
- Watch the analysis progress in the "Recent Analyses" section

### 4. View results

Once analysis is complete, click "View Results" to see the capa output.

## API Usage

capa-server provides a REST API for automation and integration.

### API Documentation

Interactive API docs are available at:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`

### Upload a file for analysis

```bash
curl -X POST \
  -F "file=@/path/to/malware.exe" \
  http://localhost:8080/api/analyze
```

Response:
```json
{
  "message": "Analysis started",
  "analysis_id": 1,
  "duplicate": false
}
```

### Check analysis status

```bash
curl http://localhost:8080/api/analyses/1
```

Response:
```json
{
  "id": 1,
  "filename": "malware.exe",
  "file_hash": "abc123...",
  "file_size": 102400,
  "created_at": "2024-11-14T10:30:00",
  "status": "completed",
  "capa_version": "7.0.0",
  "capabilities_count": 42,
  "attack_techniques": ["T1027", "T1082", ...],
  "results": { ... }
}
```

### Download JSON results

```bash
curl http://localhost:8080/api/analyses/1/download \
  -o results.json
```

### List all analyses

```bash
# Get first 100 analyses
curl http://localhost:8080/api/analyses

# Filter by status
curl "http://localhost:8080/api/analyses?status=completed&limit=50"
```

### Delete an analysis

```bash
curl -X DELETE http://localhost:8080/api/analyses/1
```

## Python Integration

```python
import requests

# Upload file
with open('malware.exe', 'rb') as f:
    response = requests.post(
        'http://localhost:8080/api/analyze',
        files={'file': f}
    )
    analysis_id = response.json()['analysis_id']

# Poll for completion
import time
while True:
    result = requests.get(
        f'http://localhost:8080/api/analyses/{analysis_id}'
    ).json()

    if result['status'] == 'completed':
        print(f"Found {result['capabilities_count']} capabilities")
        print(f"ATT&CK: {result['attack_techniques']}")
        break
    elif result['status'] == 'failed':
        print(f"Analysis failed: {result['error_message']}")
        break

    time.sleep(2)

# Download full results
response = requests.get(
    f'http://localhost:8080/api/analyses/{analysis_id}/download'
)
with open('results.json', 'wb') as f:
    f.write(response.content)
```

## Batch Processing

Process multiple files:

```bash
#!/bin/bash
# batch-analyze.sh

for file in samples/*.exe; do
    echo "Analyzing $file..."
    curl -X POST \
        -F "file=@$file" \
        http://localhost:8080/api/analyze
    sleep 1
done
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Malware Analysis
on: [push]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Start capa-server
        run: |
          docker-compose up -d
          sleep 10

      - name: Analyze binary
        run: |
          curl -X POST \
            -F "file=@suspicious.exe" \
            http://localhost:8080/api/analyze
```

## Configuration

### Environment Variables

Create a `.env` file:

```bash
CAPA_RULES_PATH=/app/rules
MAX_FILE_SIZE_MB=200
DEBUG=true
```

### Custom Rules

Mount custom capa rules:

```yaml
# docker-compose.yml
services:
  capa-server:
    volumes:
      - ./my-rules:/app/custom-rules
    environment:
      - CAPA_RULES_PATH=/app/custom-rules
```

## Troubleshooting

### Analysis fails with "Unsupported format"

capa supports PE, ELF, .NET modules, shellcode, and sandbox reports (CAPE, VMRay, DRAKVUF). If your file isn't one of these formats, analysis will fail.

### Service won't start

Check logs:
```bash
docker-compose logs -f
```

### Out of disk space

Clean old analyses:
```bash
curl -X DELETE http://localhost:8080/api/analyses/1
curl -X DELETE http://localhost:8080/api/analyses/2
# ... or clean all data
make clean
```

### Performance issues

Large files may take several minutes to analyze. Consider:
- Increasing container resources
- Setting `MAX_FILE_SIZE_MB` lower
- Running analysis as a separate background service

## Security Considerations

### Running in Production

capa-server is designed for **internal lab use**. For production:

1. **Add authentication** - Use a reverse proxy (nginx/Traefide) with basic auth or OAuth
2. **Network isolation** - Run in an isolated network segment
3. **Resource limits** - Configure Docker resource constraints
4. **Read-only filesystem** - Uncomment security options in docker-compose.yml
5. **Regular updates** - Keep capa and rules up to date

### Handling Malware Safely

- Run in an isolated VM or container environment
- Don't expose to the internet
- Use file size limits
- Monitor disk usage
- Consider running with network disabled

## Maintenance

### Update capa rules

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Backup database

```bash
cp data/capa.db data/capa.db.backup
```

### View statistics

```bash
curl http://localhost:8080/api/info
```
