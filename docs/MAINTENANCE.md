# Maintenance Guide for capa-server

**Last Updated:** 2025-11-15

This guide covers repository cleanup, signature updates, and system maintenance.

---

## 1. Repository Cleanup

### Files Safe to Remove (Development Only)

#### capa-server Repository

**Development/Testing Files** (safe to delete):
```bash
# Test scripts
rm test-api.sh
rm INSTALL_SUMMARY.txt

# Development helpers (optional - useful for contributors)
# rm Makefile
# rm .env.example
```

**Keep these files:**
-  `README.md` and all documentation (*.md)
-  `Dockerfile` and `docker-compose.yml` - Required for container
-  `.dockerignore` - Optimizes builds
-  `requirements.txt` - Python dependencies
-  `app/` - Application code
-  `static/` - Web UI
-  `data/` - Runtime data (databases, uploads)
-  `.gitignore` - Version control
-  `LICENSE` - Legal

#### badsign Repository

**Development Artifacts** (safe to clean):
```bash
cd /home/robb/tools/badsign

# Remove Python cache (regenerated automatically)
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
rm -rf .pytest_cache/

# Remove egg-info (regenerated on install)
rm -rf badsign.egg-info/

# Remove example/test files if present
rm -rf data/  # Sample data from development
```

**Keep these files:**
-  `badsign/` - Source code
-  `tests/` - Unit tests (for contributors)
-  `examples/` - Example usage
-  `docs/` - Documentation
-  `requirements.txt` and `requirements-dev.txt`
-  `pyproject.toml` - Package metadata
-  `README.md` and other docs
-  `.gitignore`
-  `LICENSE`

### Automated Cleanup Script

**Create `cleanup.sh` in capa-server:**
```bash
#!/bin/bash
# Clean up development artifacts

echo "Cleaning up capa-server repository..."

# Remove development test files
rm -f test-api.sh
rm -f INSTALL_SUMMARY.txt

# Clean Python cache in app/
find app/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find app/ -type f -name "*.pyc" -delete

echo " capa-server cleaned"

# Clean badsign if it exists
if [ -d "../badsign" ]; then
    echo "Cleaning up badsign repository..."
    cd ../badsign
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    rm -rf .pytest_cache/ badsign.egg-info/ data/
    echo " badsign cleaned"
fi

echo ""
echo "Cleanup complete!"
```

Make executable:
```bash
chmod +x cleanup.sh
./cleanup.sh
```

### Size Optimization

**Before cleanup:**
```bash
du -sh /home/robb/tools/capa-server
du -sh /home/robb/tools/badsign
```

**After cleanup** (removes ~1-5MB of cache):
- Smaller git repository
- Faster container builds
- Cleaner development environment

---

## 2. Signature and Database Updates

### A. capa Rules Updates

**Current Status:**
- Rules are cloned during container build from: https://github.com/mandiant/capa-rules
- Container includes rules at build time
- Rules are static (not auto-updated at runtime)

**Update Methods:**

#### Method 1: Rebuild Container (Recommended)
```bash
# Pull latest changes
cd /home/robb/tools/capa-server

# Rebuild container (pulls latest rules)
podman-compose down
podman-compose build --no-cache
podman-compose up -d

# Verify new rules count
curl http://localhost:8080/api/info | grep rules_count
```

**Frequency:** Monthly or when major capa updates released

#### Method 2: Manual Update (Advanced)
```bash
# Update rules in running container
podman exec -it capa-server bash
cd /app/rules
git pull origin main
exit

# Restart container
podman-compose restart
```

#### Method 3: Mount Custom Rules
Edit `docker-compose.yml`:
```yaml
volumes:
  - ./data:/app/data:Z
  - ./custom-rules:/app/custom-rules:Z  # Add this

environment:
  - CAPA_RULES_PATH=/app/custom-rules  # Use custom rules
```

Then manage rules outside container:
```bash
cd /home/robb/tools/capa-server
git clone https://github.com/mandiant/capa-rules.git custom-rules
cd custom-rules
git pull  # Update anytime

podman-compose restart
```

**Automation Script (`update-capa-rules.sh`):**
```bash
#!/bin/bash
# Update capa rules via container rebuild

echo "Updating capa rules..."

cd /home/robb/tools/capa-server

# Backup data
echo "Backing up data..."
cp -r data data.backup.$(date +%Y%m%d)

# Stop container
echo "Stopping container..."
podman-compose down

# Rebuild with latest rules
echo "Rebuilding with latest capa rules..."
podman-compose build --no-cache capa-server

# Start container
echo "Starting container..."
podman-compose up -d

# Wait for startup
sleep 10

# Check rules count
echo ""
echo "New rules count:"
curl -s http://localhost:8080/api/info | grep -o '"capa_rules_count":[0-9]*'

echo ""
echo " Update complete!"
```

**Frequency Recommendations:**
- **Monthly:** Check for rule updates
- **After capa release:** Rebuild when new capa version released
- **Custom rules:** Update as needed for your use case

---

### B. ClamAV Virus Database Updates

**Current Status:**
- ClamAV database updated during container build via `freshclam`
- Database is ~150MB+ and static after build
- Not auto-updated at runtime

**Update Methods:**

#### Method 1: Rebuild Container (Simplest)
```bash
# Same as capa rules update
cd /home/robb/tools/capa-server
podman-compose down
podman-compose build --no-cache
podman-compose up -d
```

**Gets you:**
- Latest ClamAV database
- Latest capa rules
- Clean rebuild

#### Method 2: Update in Running Container
```bash
# Update database in running container
podman exec -it capa-server freshclam

# Restart ClamAV daemon (if used)
podman exec -it capa-server systemctl restart clamav-daemon 2>/dev/null || true

# Test scan
podman exec -it capa-server clamscan --version
```

**Note:** Our container uses `clamscan` (command-line), not `clamd` (daemon), so no daemon restart needed.

#### Method 3: Automated Updates (Advanced)

**Add to `Dockerfile` for auto-updates:**
```dockerfile
# After the application startup, before CMD
# Install cron for scheduled updates
RUN apt-get update && apt-get install -y cron

# Create update script
RUN echo '#!/bin/bash\nfreshclam' > /usr/local/bin/update-clamav.sh && \
    chmod +x /usr/local/bin/update-clamav.sh

# Add cron job (daily at 2 AM)
RUN echo '0 2 * * * root /usr/local/bin/update-clamav.sh' >> /etc/crontab
```

**Then in startup:**
```dockerfile
CMD cron && uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**Caution:** This increases container complexity. Rebuilds are simpler and more reliable.

**Automation Script (`update-clamav.sh`):**
```bash
#!/bin/bash
# Update ClamAV database in running container

echo "Updating ClamAV virus database..."

# Check if container is running
if ! podman ps | grep -q capa-server; then
    echo "Error: capa-server container is not running"
    exit 1
fi

# Update database
echo "Running freshclam..."
podman exec capa-server freshclam

# Check database info
echo ""
echo "Database info:"
podman exec capa-server clamscan --version

echo ""
echo " ClamAV database updated!"
echo "Note: No restart required for clamscan"
```

**Frequency Recommendations:**
- **Daily-Weekly:** ClamAV databases updated multiple times per day
- **For production:** Rebuild container weekly
- **For dev/lab:** Rebuild monthly or as needed
- **After outbreaks:** Rebuild immediately to get latest signatures

---

### C. YARA Rules (Optional)

badsign generates YARA rules from capa analysis, but you may want external YARA rule sets:

**Popular YARA Rule Repositories:**
```bash
# Clone rule sets (outside container)
mkdir -p /home/robb/tools/yara-rules

# YARA-Rules project
git clone https://github.com/Yara-Rules/rules.git /home/robb/tools/yara-rules/yara-rules

# Awesome YARA
git clone https://github.com/InQuest/awesome-yara.git /home/robb/tools/yara-rules/awesome-yara

# Update rules
cd /home/robb/tools/yara-rules/yara-rules && git pull
cd /home/robb/tools/yara-rules/awesome-yara && git pull
```

**Use with badsign:**
```bash
# Test generated rules against known rule sets
cd /home/robb/tools/yara-rules
yara -r yara-rules/ /path/to/malware/sample
```

---

## 3. BoltDB Warning - Podman Database Migration

### What is the BoltDB Warning?

**The warning you see:**
```
The deprecated BoltDB database driver is in use. This driver will be removed
in the upcoming Podman 6.0 release in mid 2026. It is advised that you migrate
to SQLite to avoid issues when this occurs.
```

**Important:** This is **NOT about your capa-server SQLite database**. This is about **Podman's internal container metadata database** that tracks:
- Container configurations
- Images
- Networks
- Volumes

### Current Status

**Check your Podman database backend:**
```bash
podman info --format '{{.Host.DatabaseBackend}}'
# Output: boltdb (old) or sqlite (new)
```

### Is Migration Necessary?

**Short answer:** Not urgent, but recommended.

**Timeline:**
-  **Now (Nov 2025):** BoltDB still works fine
-  **Mid 2026:** BoltDB will be removed in Podman 6.0
-  **Action:** Migrate when convenient (before mid-2026)

**Impact if you don't migrate:**
- No immediate impact
- When Podman 6.0 releases, you'll need to migrate
- Could lose container metadata if not migrated properly

### Migration Difficulty

**Complexity: LOW **

Migration is a **one-time, 5-minute process** that requires:
1. Podman 4.7+ (you likely have this)
2. One command to migrate
3. Restart Podman

**No impact on:**
- Your containers
- Your images
- Your data volumes
- Your applications

### Migration Steps

#### Step 1: Check Podman Version
```bash
podman --version
# Need: Podman 4.7.0 or higher
```

If < 4.7.0:
```bash
# Update Podman first (Fedora)
sudo dnf upgrade podman
```

#### Step 2: Migrate Database
```bash
# Stop all containers first
podman-compose down

# Migrate Podman database
podman system migrate
# This converts BoltDB → SQLite automatically
```

**What happens:**
- Podman stops all containers (if running)
- Reads BoltDB metadata
- Writes to new SQLite database
- Updates Podman configuration

**Duration:** 10-60 seconds depending on how many containers/images you have

#### Step 3: Verify Migration
```bash
# Check new database backend
podman info --format '{{.Host.DatabaseBackend}}'
# Should output: sqlite

# Verify containers still exist
podman ps -a

# Verify images still exist
podman images
```

#### Step 4: Restart Services
```bash
# Start capa-server again
cd /home/robb/tools/capa-server
podman-compose up -d

# Verify it works
curl http://localhost:8080/health
```

#### Step 5: Cleanup (Optional)
```bash
# After verifying everything works, remove old BoltDB files
# Location: ~/.local/share/containers/storage/libpod/bolt_state.db
rm ~/.local/share/containers/storage/libpod/bolt_state.db.backup
```

### Suppressing the Warning (Temporary)

If you want to suppress the warning until you migrate:

```bash
# Add to ~/.bashrc or ~/.zshrc
export SUPPRESS_BOLTDB_WARNING=1

# Or in docker-compose.yml:
environment:
  - SUPPRESS_BOLTDB_WARNING=1
```

**Not recommended:** Just migrate instead—it's quick and painless.

### Rollback (If Needed)

If migration causes issues (unlikely):

```bash
# Podman keeps a backup
podman system reset  # WARNING: Removes all containers/images
# Then restore from backup
```

**Better:** Test migration on non-production system first.

### Migration Script

**Create `migrate-podman-to-sqlite.sh`:**
```bash
#!/bin/bash
# Migrate Podman from BoltDB to SQLite

set -e

echo "Podman BoltDB → SQLite Migration"
echo "================================="
echo ""

# Check Podman version
PODMAN_VERSION=$(podman --version | grep -oP '\d+\.\d+' | head -1)
echo "Podman version: $PODMAN_VERSION"

if [ "$(echo "$PODMAN_VERSION < 4.7" | bc)" -eq 1 ]; then
    echo "Error: Podman 4.7+ required"
    echo "Update with: sudo dnf upgrade podman"
    exit 1
fi

# Check current backend
CURRENT_DB=$(podman info --format '{{.Host.DatabaseBackend}}')
echo "Current database: $CURRENT_DB"

if [ "$CURRENT_DB" = "sqlite" ]; then
    echo " Already using SQLite! No migration needed."
    exit 0
fi

echo ""
echo "Migration Steps:"
echo "1. Stop all containers"
echo "2. Migrate database (automatic)"
echo "3. Verify migration"
echo "4. Restart containers"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled"
    exit 0
fi

# Stop all containers
echo ""
echo "[1/4] Stopping all containers..."
podman stop $(podman ps -aq) 2>/dev/null || echo "No running containers"

# Migrate
echo ""
echo "[2/4] Migrating database..."
podman system migrate

# Verify
echo ""
echo "[3/4] Verifying migration..."
NEW_DB=$(podman info --format '{{.Host.DatabaseBackend}}')
echo "New database: $NEW_DB"

if [ "$NEW_DB" != "sqlite" ]; then
    echo "Error: Migration failed!"
    exit 1
fi

echo " Migration successful!"

# Ask about restart
echo ""
echo "[4/4] Restart capa-server?"
echo "Container will be restarted automatically"

# Restart capa-server if compose file exists
if [ -f "$HOME/tools/capa-server/docker-compose.yml" ]; then
    cd "$HOME/tools/capa-server"
    podman-compose up -d
    echo " capa-server restarted"
fi

echo ""
echo "================================================================"
echo " Podman migration complete!"
echo ""
echo "Database: BoltDB → SQLite"
echo "Warning will no longer appear"
echo ""
echo "Old database backup: ~/.local/share/containers/storage/libpod/*.backup"
echo "Safe to delete after verifying everything works"
echo "================================================================"
```

Make executable:
```bash
chmod +x migrate-podman-to-sqlite.sh
./migrate-podman-to-sqlite.sh
```

---

## 4. Combined Maintenance Schedule

### Weekly (Production)
```bash
# Update ClamAV database
./update-clamav.sh
```

### Monthly
```bash
# Update all signatures
./update-capa-rules.sh  # Rebuilds container with latest rules

# Check for Podman updates
sudo dnf upgrade podman

# Clean up old data
rm -rf data.backup.*  # Keep last 3 backups only
```

### Quarterly
```bash
# Full system maintenance
./cleanup.sh  # Clean development artifacts
./migrate-podman-to-sqlite.sh  # If not done yet
podman system prune -a  # Clean unused images/containers
```

### After Major Releases
- **capa release:** Rebuild container
- **ClamAV emergency:** Rebuild for critical updates
- **Podman 6.0:** Must migrate to SQLite (mid-2026)

---

## 5. Automation with Cron

**Create `/etc/cron.d/capa-server-maintenance`:**
```cron
# Weekly ClamAV update (Sunday 2 AM)
0 2 * * 0 robb /home/robb/tools/capa-server/update-clamav.sh >> /var/log/capa-maintenance.log 2>&1

# Monthly full update (1st of month, 3 AM)
0 3 1 * * robb /home/robb/tools/capa-server/update-capa-rules.sh >> /var/log/capa-maintenance.log 2>&1

# Quarterly cleanup (Jan/Apr/Jul/Oct, 4 AM)
0 4 1 1,4,7,10 * robb /home/robb/tools/capa-server/cleanup.sh >> /var/log/capa-maintenance.log 2>&1
```

---

## Summary

| Task | Complexity | Urgency | Frequency |
|------|-----------|---------|-----------|
| **Repo cleanup** |  Easy | Low | Once |
| **capa rules update** |  Easy | Medium | Monthly |
| **ClamAV DB update** |  Easy | Medium | Weekly |
| **BoltDB → SQLite** |  Easy | Low | Once (before mid-2026) |

**Total maintenance time:** ~15 minutes/month after initial setup

All updates are **non-breaking** and can be done with **zero downtime** (brief restart needed).
