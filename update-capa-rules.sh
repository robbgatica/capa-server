#!/bin/bash
# Update capa rules by rebuilding container with latest rules from GitHub

set -e

echo "========================================="
echo "capa Rules Update"
echo "========================================="
echo ""

cd "$(dirname "$0")"

# Check if compose file exists
if [ ! -f "docker-compose.yml" ]; then
    echo "Error: docker-compose.yml not found"
    exit 1
fi

# Detect container runtime
if command -v podman &> /dev/null; then
    COMPOSE="podman-compose"
    RUNTIME="Podman"
elif command -v docker &> /dev/null; then
    COMPOSE="docker-compose"
    RUNTIME="Docker"
else
    echo "Error: Neither podman nor docker found"
    exit 1
fi

echo "Using: $RUNTIME"
echo ""

# Backup data
BACKUP_DIR="data.backup.$(date +%Y%m%d_%H%M%S)"
if [ -d "data" ]; then
    echo "[1/5] Backing up data..."
    cp -r data "$BACKUP_DIR"
    echo " Data backed up to: $BACKUP_DIR"
else
    echo "[1/5] No data directory to backup"
fi

# Stop container
echo ""
echo "[2/5] Stopping container..."
$COMPOSE down
echo " Container stopped"

# Rebuild with latest rules
echo ""
echo "[3/5] Rebuilding container with latest capa rules..."
echo "This will:"
echo "  • Clone latest capa-rules from GitHub"
echo "  • Update ClamAV virus database"
echo "  • Rebuild application"
echo ""
$COMPOSE build --no-cache capa-server
echo " Container rebuilt"

# Start container
echo ""
echo "[4/5] Starting container..."
$COMPOSE up -d
echo " Container started"

# Wait for startup
echo ""
echo "[5/5] Waiting for service to be ready..."
sleep 10

# Check health
MAX_RETRIES=12
RETRY=0
while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        break
    fi
    RETRY=$((RETRY + 1))
    if [ $RETRY -lt $MAX_RETRIES ]; then
        echo "Waiting for service... ($RETRY/$MAX_RETRIES)"
        sleep 5
    fi
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    echo ""
    echo " Warning: Service did not respond to health check"
    echo "Check logs: $COMPOSE logs"
else
    echo " Service is healthy"

    # Show updated rules count
    echo ""
    echo "========================================="
    echo "Update Complete!"
    echo "========================================="
    echo ""

    RULES_COUNT=$(curl -s http://localhost:8080/api/info | grep -o '"capa_rules_count":[0-9]*' | cut -d: -f2)
    if [ -n "$RULES_COUNT" ]; then
        echo "capa rules count: $RULES_COUNT"
    fi

    echo ""
    echo "Latest changes:"
    echo "  • capa rules: Latest from GitHub"
    echo "  • ClamAV DB:  Latest virus signatures"
    echo ""
    echo "Backup location: $BACKUP_DIR"
    echo ""
    echo "To view logs:  $COMPOSE logs -f"
    echo "To check info: curl http://localhost:8080/api/info"
fi
