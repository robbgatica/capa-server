#!/bin/bash
# Migrate Podman from BoltDB to SQLite database backend

set -e

echo "==========================================="
echo "Podman Database Migration"
echo "BoltDB → SQLite"
echo "==========================================="
echo ""

# Check if podman exists
if ! command -v podman &> /dev/null; then
    echo "Error: podman not found"
    echo "This script is only for Podman (not Docker)"
    exit 1
fi

# Check Podman version
PODMAN_VERSION=$(podman --version | grep -oP '\d+\.\d+' | head -1)
echo "Podman version: $PODMAN_VERSION"

# Version check (need 4.7+)
if [ -z "$PODMAN_VERSION" ]; then
    echo "Error: Could not detect Podman version"
    exit 1
fi

REQUIRED_VERSION="4.7"
if (( $(echo "$PODMAN_VERSION < $REQUIRED_VERSION" | bc -l) )); then
    echo ""
    echo "Error: Podman $REQUIRED_VERSION+ required for migration"
    echo "Current version: $PODMAN_VERSION"
    echo ""
    echo "Update Podman:"
    echo "  sudo dnf upgrade podman"
    exit 1
fi

echo " Version check passed"

# Check current database backend
echo ""
echo "Checking current database backend..."
CURRENT_DB=$(podman info --format '{{.Host.DatabaseBackend}}')
echo "Current database: $CURRENT_DB"

if [ "$CURRENT_DB" = "sqlite" ]; then
    echo ""
    echo "==========================================="
    echo " Already using SQLite!"
    echo "==========================================="
    echo ""
    echo "No migration needed."
    echo "The BoltDB warning should not appear."
    echo ""
    exit 0
fi

# Explain what will happen
echo ""
echo "==========================================="
echo "Migration Overview"
echo "==========================================="
echo ""
echo "This will:"
echo "  1. Stop all running containers"
echo "  2. Migrate Podman metadata: BoltDB → SQLite"
echo "  3. Verify migration succeeded"
echo "  4. Restart capa-server"
echo ""
echo "What's migrated:"
echo "  • Container configurations"
echo "  • Image metadata"
echo "  • Volume metadata"
echo "  • Network configurations"
echo ""
echo "What's preserved:"
echo "   All containers"
echo "   All images"
echo "   All volumes (your data)"
echo "   All networks"
echo ""
echo "Duration: ~30-60 seconds"
echo "Downtime: Brief (containers stopped during migration)"
echo ""
read -p "Continue with migration? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled"
    exit 0
fi

# List containers before migration
echo ""
echo "==========================================="
echo "Step 1: Pre-migration Status"
echo "==========================================="
echo ""
echo "Containers before migration:"
podman ps -a --format "table {{.Names}}\t{{.Status}}"

# Stop all containers
echo ""
echo "==========================================="
echo "Step 2: Stopping Containers"
echo "==========================================="
echo ""

RUNNING_CONTAINERS=$(podman ps -q)
if [ -n "$RUNNING_CONTAINERS" ]; then
    echo "Stopping containers..."
    podman stop $RUNNING_CONTAINERS
    echo " Containers stopped"
else
    echo "No running containers to stop"
fi

# Perform migration
echo ""
echo "==========================================="
echo "Step 3: Migrating Database"
echo "==========================================="
echo ""
echo "Running: podman system migrate"
echo ""

podman system migrate

echo ""
echo " Migration complete"

# Verify migration
echo ""
echo "==========================================="
echo "Step 4: Verification"
echo "==========================================="
echo ""

NEW_DB=$(podman info --format '{{.Host.DatabaseBackend}}')
echo "New database backend: $NEW_DB"

if [ "$NEW_DB" != "sqlite" ]; then
    echo ""
    echo " Error: Migration failed!"
    echo "Database is still: $NEW_DB"
    echo ""
    echo "Check Podman logs for errors:"
    echo "  journalctl -xe | grep podman"
    exit 1
fi

echo " Verification passed"

# Check containers still exist
echo ""
echo "Containers after migration:"
podman ps -a --format "table {{.Names}}\t{{.Status}}"

# Restart capa-server if compose file exists
echo ""
echo "==========================================="
echo "Step 5: Restarting Services"
echo "==========================================="
echo ""

CAPA_SERVER_DIR="$(dirname "$0")"
if [ -f "$CAPA_SERVER_DIR/docker-compose.yml" ]; then
    cd "$CAPA_SERVER_DIR"

    echo "Restarting capa-server..."

    if command -v podman-compose &> /dev/null; then
        podman-compose up -d
    else
        echo "Note: podman-compose not found"
        echo "Start containers manually:"
        echo "  podman start capa-server"
    fi

    # Wait and check health
    sleep 5
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        echo " capa-server is running"
    else
        echo " Warning: capa-server health check failed"
        echo "Check logs: podman logs capa-server"
    fi
else
    echo "Note: docker-compose.yml not found"
    echo "Start containers manually:"
    echo "  podman start <container-name>"
fi

# Show cleanup info
echo ""
echo "==========================================="
echo " Migration Complete!"
echo "==========================================="
echo ""
echo "Results:"
echo "  Old database: BoltDB"
echo "  New database: SQLite"
echo "  Status:       SUCCESS "
echo ""
echo "Benefits:"
echo "   BoltDB warning will no longer appear"
echo "   Better performance and reliability"
echo "   Compatible with Podman 6.0+"
echo ""
echo "Cleanup (optional):"
echo "  Old database backup created at:"
echo "  ~/.local/share/containers/storage/libpod/bolt_state.db.backup"
echo ""
echo "  Safe to delete after verifying everything works:"
echo "  rm ~/.local/share/containers/storage/libpod/bolt_state.db.backup"
echo ""
echo "Verify capa-server:"
echo "  curl http://localhost:8080/api/info"
echo ""
