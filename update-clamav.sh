#!/bin/bash
# Update ClamAV virus database in running container

set -e

echo "========================================="
echo "ClamAV Virus Database Update"
echo "========================================="
echo ""

# Detect container runtime
if command -v podman &> /dev/null; then
    RUNTIME="podman"
elif command -v docker &> /dev/null; then
    RUNTIME="docker"
else
    echo "Error: Neither podman nor docker found"
    exit 1
fi

CONTAINER_NAME="capa-server"

# Check if container is running
if ! $RUNTIME ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
    echo "Error: $CONTAINER_NAME container is not running"
    echo ""
    echo "Start it with: podman-compose up -d"
    exit 1
fi

echo "Container: $CONTAINER_NAME"
echo "Runtime:   $RUNTIME"
echo ""

# Show current database info
echo "[1/3] Current ClamAV version:"
$RUNTIME exec $CONTAINER_NAME clamscan --version | head -3
echo ""

# Update database
echo "[2/3] Updating virus database..."
echo "This may take 1-2 minutes..."
echo ""

$RUNTIME exec $CONTAINER_NAME freshclam

echo ""
echo " Database updated"

# Show new database info
echo ""
echo "[3/3] Updated ClamAV version:"
$RUNTIME exec $CONTAINER_NAME clamscan --version | head -3

echo ""
echo "========================================="
echo "Update Complete!"
echo "========================================="
echo ""
echo "ClamAV virus database has been updated."
echo ""
echo "Notes:"
echo "  • No container restart required"
echo "  • clamscan uses updated database immediately"
echo "  • Database persists until container rebuild"
echo ""
echo "For automatic updates, rebuild container weekly:"
echo "  ./update-capa-rules.sh"
echo ""
