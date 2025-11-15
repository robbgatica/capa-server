#  capa-server Documentation Index

**Quick navigation guide to all documentation files**

Last Updated: 2025-11-15

---

##  Getting Started (Start Here!)

| Document | Description | Lines | When to Read |
|----------|-------------|-------|--------------|
| [README.md](../README.md) | **Main documentation** - Features, API reference, quick start | 363 | First read |
| [QUICKSTART.md](QUICKSTART.md) | Get started in 5 minutes | 54 | Right after README |
| [USAGE.md](USAGE.md) | Detailed usage instructions | 174 | When ready to use |
| [FEATURES_SUMMARY.md](FEATURES_SUMMARY.md) | **Complete feature reference** - All capabilities explained | 461 | Reference guide |

---

##  Signature Generation Tools

| Document | Description | Lines | When to Read |
|----------|-------------|-------|--------------|
| [BADSIGN_CLI.md](BADSIGN_CLI.md) | **Standalone CLI reference** - Complete command documentation | 504 | Using CLI tools |
| [SEPARATE_REPO_GUIDE.md](SEPARATE_REPO_GUIDE.md) | **Copy to separate repo** - How to extract badsign | 453 | Creating standalone repo |
| [QUICKSTART_YARA.md](QUICKSTART_YARA.md) | Quick guide to YARA generation | 259 | YARA workflow |
| [YARA_INTEGRATION.md](YARA_INTEGRATION.md) | YARA integration details | 404 | Deep dive on YARA |
| [BADSIGN_ANALYSIS.md](BADSIGN_ANALYSIS.md) | Analysis of badsign implementation | 941 | Understanding internals |

---

##  Container & Deployment

| Document | Description | Lines | When to Read |
|----------|-------------|-------|--------------|
| [PODMAN.md](PODMAN.md) | Podman-specific instructions (Fedora/RHEL) | 169 | Using Podman |
| [CONTAINER_COMPATIBILITY.md](CONTAINER_COMPATIBILITY.md) | Docker/Podman compatibility guide | 125 | Container issues |
| [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) | ClamAV integration implementation | 534 | Understanding integration |
| [WORKFLOWS.md](WORKFLOWS.md) | Analysis workflows and examples | 377 | Workflow planning |

---

##  Development

| Document | Description | Lines | When to Read |
|----------|-------------|-------|--------------|
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Architecture and design overview | 219 | Contributing |
| [NEXT_STEPS.md](NEXT_STEPS.md) | Development roadmap | 154 | Future plans |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines | 123 | Before contributing |

---

##  Documentation by Use Case

### "I want to analyze malware"
1. Read: [README.md](../README.md) - Overview
2. Read: [QUICKSTART.md](QUICKSTART.md) - Setup
3. Read: [USAGE.md](USAGE.md) - How to use
4. Reference: [FEATURES_SUMMARY.md](FEATURES_SUMMARY.md) - All features

### "I want to generate YARA rules"
1. Read: [QUICKSTART_YARA.md](QUICKSTART_YARA.md) - Quick start
2. Read: [BADSIGN_CLI.md](BADSIGN_CLI.md#2-capa-to-yara) - CLI reference
3. Reference: [YARA_INTEGRATION.md](YARA_INTEGRATION.md) - Deep dive

### "I want to generate ClamAV signatures"
1. Read: [README.md](README.md#clamav-integration) - Overview
2. Read: [BADSIGN_CLI.md](BADSIGN_CLI.md#1-generate) - CLI reference
3. Reference: [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) - Implementation

### "I want to use badsign standalone"
1. Read: [BADSIGN_CLI.md](BADSIGN_CLI.md) - Complete CLI guide
2. Read: [SEPARATE_REPO_GUIDE.md](SEPARATE_REPO_GUIDE.md) - Extraction guide
3. Reference: [BADSIGN_ANALYSIS.md](BADSIGN_ANALYSIS.md) - Internals

### "I'm using Podman on Fedora/RHEL"
1. Read: [PODMAN.md](PODMAN.md) - Podman guide
2. Read: [CONTAINER_COMPATIBILITY.md](CONTAINER_COMPATIBILITY.md) - Troubleshooting
3. Reference: [QUICKSTART.md](QUICKSTART.md) - Basic setup

### "I want to contribute"
1. Read: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Architecture
2. Read: [CONTRIBUTING.md](CONTRIBUTING.md) - Guidelines
3. Read: [NEXT_STEPS.md](NEXT_STEPS.md) - Roadmap

---

##  File Size Reference

```
Total documentation: ~150 KB across 16 files

Largest files:
- BADSIGN_ANALYSIS.md    33 KB (941 lines)
- README.md                    11 KB (363 lines)
- BADSIGN_CLI.md         13 KB (504 lines)
- FEATURES_SUMMARY.md          13 KB (461 lines)
- SEPARATE_REPO_GUIDE.md       12 KB (453 lines)
```

---

##  Quick Links by Topic

### Container Management
- [PODMAN.md](PODMAN.md) - Podman usage
- [CONTAINER_COMPATIBILITY.md](CONTAINER_COMPATIBILITY.md) - Compatibility
- [README.md](README.md#quick-start) - Quick start

### API Reference
- [README.md](README.md#api-endpoints) - All endpoints
- `http://localhost:8080/docs` - Interactive Swagger UI
- [FEATURES_SUMMARY.md](FEATURES_SUMMARY.md#-api-endpoints) - Endpoint table

### Signature Generation
- [BADSIGN_CLI.md](BADSIGN_CLI.md) - CLI reference
- [YARA_INTEGRATION.md](YARA_INTEGRATION.md) - YARA details
- [QUICKSTART_YARA.md](QUICKSTART_YARA.md) - Quick YARA guide

### Security
- [README.md](README.md#security-considerations) - Security notes
- [USAGE.md](USAGE.md) - Safe usage practices
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Design decisions

### Troubleshooting
- [PODMAN.md](PODMAN.md#troubleshooting) - Podman issues
- [CONTAINER_COMPATIBILITY.md](CONTAINER_COMPATIBILITY.md) - Container problems
- [README.md](README.md#database-management) - Database issues

---

##  Reading Order Recommendations

### For End Users (Analysts)
1. [README.md](../README.md) - Overview
2. [QUICKSTART.md](QUICKSTART.md) - Setup
3. [USAGE.md](USAGE.md) - Usage
4. [FEATURES_SUMMARY.md](FEATURES_SUMMARY.md) - Reference

**Optional:**
- [QUICKSTART_YARA.md](QUICKSTART_YARA.md) - If using YARA
- [PODMAN.md](PODMAN.md) - If using Podman
- [WORKFLOWS.md](WORKFLOWS.md) - Workflow examples

### For Tool Developers
1. [README.md](../README.md) - Overview
2. [BADSIGN_CLI.md](BADSIGN_CLI.md) - CLI tools
3. [SEPARATE_REPO_GUIDE.md](SEPARATE_REPO_GUIDE.md) - Standalone usage
4. [BADSIGN_ANALYSIS.md](BADSIGN_ANALYSIS.md) - Implementation

### For Contributors
1. [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Architecture
2. [CONTRIBUTING.md](CONTRIBUTING.md) - Guidelines
3. [NEXT_STEPS.md](NEXT_STEPS.md) - Roadmap
4. [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) - Recent work

---

##  Finding Information

### Search Tips

**By keyword:**
```bash
# Search all documentation
grep -r "keyword" *.md

# Search specific topic
grep -r "YARA" *.md
grep -r "ClamAV" *.md
grep -r "API" *.md
```

**By feature:**
- Upload: [USAGE.md](USAGE.md), [README.md](README.md#api-endpoints)
- YARA: [QUICKSTART_YARA.md](QUICKSTART_YARA.md), [YARA_INTEGRATION.md](YARA_INTEGRATION.md)
- ClamAV: [README.md](README.md#clamav-integration), [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)
- Standalone: [BADSIGN_CLI.md](BADSIGN_CLI.md), [SEPARATE_REPO_GUIDE.md](SEPARATE_REPO_GUIDE.md)

**By problem:**
- Container won't start: [PODMAN.md](PODMAN.md), [CONTAINER_COMPATIBILITY.md](CONTAINER_COMPATIBILITY.md)
- API errors: [README.md](README.md#api-endpoints), `http://localhost:8080/docs`
- Database errors: [README.md](README.md#database-management)
- Signature errors: [BADSIGN_CLI.md](BADSIGN_CLI.md#troubleshooting)

---

##  Document Status

| Type | Count | Status |
|------|-------|--------|
| User Guides | 5 |  Complete |
| Tool References | 5 |  Complete |
| Container Guides | 4 |  Complete |
| Development Docs | 3 |  Complete |
| **Total** | **16** | ** All Complete** |

---

##  Keep Documentation Current

When updating the project:

1. **Update README.md** - For any new features or API changes
2. **Update FEATURES_SUMMARY.md** - Add new features to the reference
3. **Update BADSIGN_CLI.md** - For CLI command changes
4. **Update this index** - When adding new documentation files

---

##  Still Can't Find What You Need?

1. **Check the main README first:** [README.md](../README.md)
2. **Search all docs:** `grep -r "your search" /home/robb/tools/capa-server/*.md`
3. **Check API docs:** `http://localhost:8080/docs`
4. **Look at examples:** [WORKFLOWS.md](WORKFLOWS.md)
5. **View logs:** `podman-compose logs -f` or `docker-compose logs -f`

---

**Tip:** Use your browser's "Find in page" (Ctrl+F) to search within this index, then click the links to jump to the relevant documentation.

---

**Documentation Home:** [README.md](../README.md)
**Quick Start:** [QUICKSTART.md](QUICKSTART.md)
**Complete Reference:** [FEATURES_SUMMARY.md](FEATURES_SUMMARY.md)
