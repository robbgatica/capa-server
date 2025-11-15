# Container Runtime Compatibility

capa-server is **fully compatible** with both Docker and Podman.

## Design Decisions for Compatibility

### 1. Standard Dockerfile/Containerfile

The project uses a standard `Dockerfile` that follows OCI specifications, which both Docker and Podman support. We also provide a `Containerfile` symlink (Podman's preferred naming).

```bash
# Both work identically
docker build -f Dockerfile -t capa-server .
podman build -f Containerfile -t capa-server .
```

### 2. No Docker-Specific Features

The Dockerfile avoids Docker-specific features that Podman doesn't support:

-  Uses standard `FROM`, `RUN`, `COPY`, `CMD`
-  No BuildKit-specific syntax
-  No Docker-specific networking
-  Standard health checks
-  Standard volume mounts

### 3. Auto-Detecting Makefile

The `Makefile` automatically detects which runtime is available:

```bash
$ make help
Detected runtime: Podman  # on Fedora

$ make up
Starting capa-server with Podman...
```

On systems with Docker, it will use Docker instead.

### 4. Compose File Compatibility

The `docker-compose.yml` is compatible with both:
- `docker-compose` (Docker)
- `podman-compose` (Podman)

## Runtime-Specific Notes

### Docker

**Works with:**
- Docker Desktop (Mac/Windows)
- Docker Engine (Linux)
- Docker Compose

**Command examples:**
```bash
docker build -t capa-server .
docker-compose up -d
```

### Podman

**Works with:**
- Podman (rootless or rootful)
- podman-compose
- Podman pods (alternative to compose)

**Command examples:**
```bash
podman build -t capa-server .
podman-compose up -d

# Or rootless
podman run -p 8080:8080 -v ./data:/app/data:Z capa-server
```

**SELinux Note:** On Fedora/RHEL, add `:Z` to volume mounts:
```bash
-v ./data:/app/data:Z
```

## Tested Environments

| Platform | Runtime | Version | Status |
|----------|---------|---------|--------|
| Fedora 43 | Podman | 5.x |  Designed for |
| RHEL 9 | Podman | 4.x |  Should work |
| Ubuntu 22.04 | Docker | 24.x |  Should work |
| macOS | Docker Desktop | 24.x |  Should work |
| Windows | Docker Desktop | 24.x |  Should work |

## Switching Between Runtimes

You can switch between Docker and Podman without changing any files:

```bash
# If both are installed, set preference
export CONTAINER_RUNTIME=podman  # or docker

# The Makefile will auto-detect
make up
```

Or use directly:

```bash
# Use Podman explicitly
podman-compose up -d

# Use Docker explicitly
docker-compose up -d
```

## Best Practices by Platform

### Fedora/RHEL (Podman)
```bash
# Install Podman
sudo dnf install podman podman-compose

# Run rootless
podman-compose up -d

# Use systemd for auto-start
podman generate systemd --name capa-server --files
```

### Ubuntu/Debian (Docker)
```bash
# Install Docker
sudo apt install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Run
docker-compose up -d
```

### macOS/Windows (Docker Desktop)
```bash
# Install Docker Desktop from website

# Run
docker-compose up -d
```

## Troubleshooting

### Volume Permission Issues

**Podman (SELinux):**
```bash
# Use :Z flag
podman run -v ./data:/app/data:Z capa-server

# Or relabel manually
podman unshare chown -R 0:0 data/
```

**Docker:**
```bash
# Usually no special handling needed
docker run -v ./data:/app/data capa-server

# If permission issues, fix ownership
sudo chown -R $USER:$USER data/
```

### Port Binding Issues

**Podman rootless:**
```bash
# Ports < 1024 need special handling
# Use port 8080 (recommended)

# Or enable unprivileged ports
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
```

**Docker:**
```bash
# Works for all ports
docker run -p 80:8080 capa-server
```

### Compose Command Not Found

**Podman:**
```bash
sudo dnf install podman-compose
# or
pip install podman-compose
```

**Docker:**
```bash
# Docker Desktop includes compose
# or install separately
sudo apt install docker-compose
```

## Why Both Work

1. **OCI Standard**: Both implement Open Container Initiative specs
2. **Compatible APIs**: Podman mimics Docker's CLI
3. **Standard Dockerfiles**: We use only standard features
4. **No daemon dependency**: Code doesn't rely on Docker daemon
5. **Standard networking**: Uses standard port mappings

## Future Considerations

If we add features, we'll maintain compatibility:

-  Kubernetes manifests (work with both)
-  Standard health checks
-  Standard environment variables
-  No runtime-specific extensions

## Conclusion

**You can use capa-server with whichever container runtime you prefer.**

For Fedora users: **Podman is recommended** (it's the default)
For others: **Docker works great too**

The Makefile will auto-detect and "just work" on any platform.
