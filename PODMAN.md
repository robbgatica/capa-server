# Running capa-server with Podman

Podman is a daemonless container engine that's popular on Fedora and RHEL systems.

## Prerequisites

```bash
# On Fedora
sudo dnf install podman podman-compose

# Verify installation
podman --version
podman-compose --version
```

## Quick Start with podman-compose

```bash
cd ~/tools/capa-server

# Build and start (using podman-compose)
podman-compose up -d

# Check status
podman-compose ps

# View logs
podman-compose logs -f

# Stop
podman-compose down
```

## Manual Podman Commands (without compose)

### Build the Image

```bash
podman build -t capa-server:latest .
```

### Run the Container

```bash
# Create data directories
mkdir -p data/uploads data/results

# Run container
podman run -d \
  --name capa-server \
  -p 8080:8080 \
  -v ./data:/app/data:Z \
  -e CAPA_RULES_PATH=/app/rules \
  -e DATABASE_PATH=/app/data/capa.db \
  -e UPLOAD_DIR=/app/data/uploads \
  -e RESULTS_DIR=/app/data/results \
  capa-server:latest

# Check logs
podman logs -f capa-server

# Stop container
podman stop capa-server
podman rm capa-server
```

### Important: SELinux Context (`:Z` flag)

On Fedora/RHEL with SELinux enabled, use the `:Z` flag for volumes:

```bash
-v ./data:/app/data:Z
```

This tells Podman to relabel the volume for container access.

## Rootless Podman (Recommended)

Podman can run rootless (without sudo), which is more secure:

```bash
# No sudo needed!
podman build -t capa-server .
podman run -d -p 8080:8080 --name capa-server capa-server:latest
```

### Port Binding Below 1024

If you want to use ports below 1024 (like port 80):

```bash
# Option 1: Use port 8080 and reverse proxy
# (Recommended)

# Option 2: Enable unprivileged port binding
sudo sysctl net.ipv4.ip_unprivileged_port_start=80

# Option 3: Run as root (not recommended)
sudo podman run -d -p 80:8080 capa-server
```

## Using Podman with systemd

Generate a systemd service for automatic startup:

```bash
# Run container once
podman run -d \
  --name capa-server \
  -p 8080:8080 \
  -v ./data:/app/data:Z \
  capa-server:latest

# Generate systemd unit file
podman generate systemd --name capa-server --files

# Install as user service
mkdir -p ~/.config/systemd/user/
mv container-capa-server.service ~/.config/systemd/user/

# Enable and start
systemctl --user daemon-reload
systemctl --user enable container-capa-server.service
systemctl --user start container-capa-server.service

# Check status
systemctl --user status container-capa-server.service

# Enable linger (keeps service running after logout)
loginctl enable-linger $USER
```

## Podman Pod (Alternative to docker-compose)

Podman pods are like Kubernetes pods - multiple containers sharing network:

```bash
# Create pod
podman pod create --name capa-pod -p 8080:8080

# Run container in pod
podman run -d \
  --pod capa-pod \
  --name capa-server \
  -v ./data:/app/data:Z \
  capa-server:latest

# Manage pod
podman pod ps
podman pod stop capa-pod
podman pod start capa-pod
podman pod rm capa-pod
```

## Known Differences from Docker

### 1. Volume Permissions

Podman runs rootless, so volume ownership may differ:

```bash
# If you get permission errors
podman unshare chown -R 0:0 data/
```

### 2. Network Differences

Podman uses different network drivers:

```bash
# List networks
podman network ls

# Create custom network
podman network create capa-network
```

### 3. Health Checks

Health checks work the same but might have different timing:

```bash
# Check container health
podman healthcheck run capa-server
```

## Troubleshooting

### "permission denied" on volumes

```bash
# Add :Z flag for SELinux
-v ./data:/app/data:Z

# Or disable SELinux labeling (less secure)
-v ./data:/app/data:z
```

### "port already in use"

```bash
# Check what's using the port
ss -tulpn | grep 8080

# Use different port
podman run -p 9080:8080 ...
```

### Container won't start

```bash
# Check logs
podman logs capa-server

# Check events
podman events --filter container=capa-server

# Inspect container
podman inspect capa-server
```

### podman-compose not found

```bash
# Install on Fedora
sudo dnf install podman-compose

# Or use pip
pip install podman-compose
```

## Performance Considerations

Podman rootless may have slight performance differences:

- **Slightly slower** for intensive I/O due to user namespace overhead
- **More secure** because it doesn't require root
- **Better isolation** between containers and host

For most DFIR use cases, the performance difference is negligible.

## Migration from Docker

If you're switching from Docker to Podman:

```bash
# Alias podman as docker (optional)
alias docker=podman
alias docker-compose=podman-compose

# Add to ~/.bashrc to make permanent
echo "alias docker=podman" >> ~/.bashrc
echo "alias docker-compose=podman-compose" >> ~/.bashrc
```

## Best Practices for Fedora/RHEL

1. **Use rootless Podman** - More secure, no daemon
2. **Use `:Z` for volumes** - Proper SELinux contexts
3. **Use systemd units** - Better integration with Fedora
4. **Enable linger** - Keep services running
5. **Use podman-compose** - Easiest for development

## Example: Full Fedora Setup

```bash
# Install Podman
sudo dnf install podman podman-compose

# Clone project
cd ~/tools/capa-server

# Build
podman build -t capa-server .

# Create data dir
mkdir -p data

# Run with systemd
podman run -d \
  --name capa-server \
  -p 8080:8080 \
  -v ./data:/app/data:Z \
  capa-server:latest

# Generate systemd service
podman generate systemd --name capa-server --files --new
mkdir -p ~/.config/systemd/user/
mv container-capa-server.service ~/.config/systemd/user/

# Enable auto-start
systemctl --user daemon-reload
systemctl --user enable container-capa-server.service
systemctl --user start container-capa-server.service
loginctl enable-linger $USER

# Verify
systemctl --user status container-capa-server.service
curl http://localhost:8080/health
```

## Conclusion

**Yes, capa-server works great with Podman!**

For Fedora users, Podman is actually the **recommended** approach since:
- It's the default container engine on Fedora
- Rootless by default (more secure)
- Better systemd integration
- No daemon overhead

Just use `podman-compose` for the easiest experience, or systemd units for production.
