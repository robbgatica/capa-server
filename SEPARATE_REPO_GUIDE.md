# Copying badsign to a Separate Repository

> **Generating signatures for bad stuff, period.**

This guide explains how to copy the `badsign` tool to a separate, standalone repository for independent distribution and development.

## Overview

`badsign` is already designed as a standalone library and can be separated from capa-server without modifications. It's currently located at:

```
/home/robb/tools/badsign/
```

## Files to Copy

### Required Files

Copy the entire directory structure:

```bash
badsign/
├── clamav_siggen/              # Main package (REQUIRED)
│   ├── __init__.py             # Package initialization
│   ├── capa_parser.py          # capa JSON parsing
│   ├── cli.py                  # Command-line interface
│   ├── core.py                 # ClamAV signature generation
│   ├── utils.py                # Utility functions
│   └── yara_generator.py       # YARA rule generation
│
├── tests/                      # Unit tests (RECOMMENDED)
│   ├── __init__.py
│   ├── test_capa_parser.py
│   ├── test_core.py
│   └── test_yara_generator.py
│
├── examples/                   # Example files (RECOMMENDED)
│   └── (sample analysis files)
│
├── docs/                       # Documentation (RECOMMENDED)
│   └── CAPA_TO_YARA.md        # capa-to-YARA conversion guide
│
├── requirements.txt            # Runtime dependencies (REQUIRED)
├── requirements-dev.txt        # Development dependencies (OPTIONAL)
├── pyproject.toml             # Modern Python packaging (REQUIRED)
├── setup.py                   # Legacy setup (OPTIONAL, for backward compatibility)
├── README.md                  # Main documentation (REQUIRED)
├── LICENSE                    # Apache 2.0 license (REQUIRED)
├── .gitignore                 # Git ignore rules (RECOMMENDED)
└── Makefile                   # Build automation (OPTIONAL)
```

## Step-by-Step Copy Process

### Option 1: Create New Git Repository (Recommended)

```bash
# 1. Create new directory for the standalone repo
mkdir ~/projects/badsign-standalone
cd ~/projects/badsign-standalone

# 2. Initialize git repository
git init

# 3. Copy files from original location
cp -r /home/robb/tools/badsign/clamav_siggen ./
cp -r /home/robb/tools/badsign/tests ./
cp -r /home/robb/tools/badsign/examples ./
cp -r /home/robb/tools/badsign/docs ./
cp /home/robb/tools/badsign/requirements.txt ./
cp /home/robb/tools/badsign/requirements-dev.txt ./
cp /home/robb/tools/badsign/pyproject.toml ./
cp /home/robb/tools/badsign/README.md ./
cp /home/robb/tools/badsign/LICENSE ./
cp /home/robb/tools/badsign/.gitignore ./
cp /home/robb/tools/badsign/Makefile ./

# 4. Verify structure
tree -L 2

# 5. Initial commit
git add .
git commit -m "Initial commit: badsign standalone package"

# 6. Create GitHub/GitLab repository and push
git remote add origin https://github.com/yourusername/badsign.git
git branch -M main
git push -u origin main
```

### Option 2: Direct Archive

```bash
# Create a distributable archive
cd /home/robb/tools/
tar -czf badsign-standalone.tar.gz \
    badsign/clamav_siggen/ \
    badsign/tests/ \
    badsign/examples/ \
    badsign/docs/ \
    badsign/requirements.txt \
    badsign/requirements-dev.txt \
    badsign/pyproject.toml \
    badsign/README.md \
    badsign/LICENSE \
    badsign/.gitignore \
    badsign/Makefile

# Extract elsewhere
mkdir ~/projects/badsign
cd ~/projects/badsign
tar -xzf ~/tools/badsign-standalone.tar.gz
mv badsign/* .
rmdir badsign
```

## Dependencies

### Runtime Dependencies (requirements.txt)

```
lief>=0.13.0           # Cross-platform binary parsing
pefile>=2023.0.0       # PE file analysis
click>=8.0.0           # CLI framework
```

### Development Dependencies (requirements-dev.txt)

```
pytest>=7.0.0          # Testing framework
pytest-cov>=4.0.0      # Coverage reporting
mypy>=1.0.0            # Type checking
pylint>=2.15.0         # Code linting
black>=23.0.0          # Code formatting
```

## Installation of Standalone Package

After copying to a separate repository, users can install it:

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/badsign.git
cd badsign

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Verify installation
badsign --version
```

### From PyPI (Future)

After publishing to PyPI:

```bash
pip install badsign
```

## No Modifications Needed

The package is **already standalone** and requires **no code changes** to work independently:

 **Self-contained** - No dependencies on capa-server
 **CLI ready** - Full command-line interface via Click
 **Library ready** - Can be imported as a Python module
 **Cross-platform** - Works on Linux, macOS, Windows
 **Well-documented** - Comprehensive README and docstrings

## Integration Examples

### As a Standalone CLI Tool

```bash
# After installation
badsign capa-to-yara analysis.json -o rule.yar
badsign generate malware.exe --name "Malware" -o sigs.ndb
```

### As a Python Library

```python
from clamav_siggen import ClamAVSigGen
from clamav_siggen.yara_generator import YaraGenerator
from clamav_siggen.capa_parser import CapaParser

# Use in your own projects
siggen = ClamAVSigGen(file_path="malware.exe")
signatures = siggen.generate_all(name="Malware")
```

### Integration with Other Projects

```python
# In another project's requirements.txt
badsign>=1.0.0

# In your code
from clamav_siggen import ClamAVSigGen

def analyze_sample(file_path):
    siggen = ClamAVSigGen(file_path=file_path)
    return siggen.generate_all(name="DetectedMalware")
```

## Relationship with capa-server

After separation, the two projects remain compatible:

### capa-server uses badsign

In capa-server's `requirements.txt`:

```
# Option 1: Install from PyPI (when published)
badsign>=1.0.0

# Option 2: Install from git repository
git+https://github.com/yourusername/badsign.git

# Option 3: Install from local path (development)
-e /path/to/badsign
```

In capa-server's `app/main.py`:

```python
from clamav_siggen import ClamAVSigGen
from clamav_siggen.yara_generator import YaraGenerator
from clamav_siggen.capa_parser import CapaParser

# capa-server endpoints use the library
@app.get("/api/analyses/{id}/generate-yara")
async def generate_yara(id: int):
    # ... load capa results
    parser = CapaParser(capa_dict=capa_data)
    generator = YaraGenerator(parser)
    return generator.generate_rule()
```

### Independent Development

- **badsign** can be developed, tested, and released independently
- **capa-server** pins a specific version for stability
- Both projects can evolve at their own pace

## Publishing to PyPI (Optional)

To make the package publicly available:

### 1. Update pyproject.toml

```toml
[project]
name = "badsign"
version = "1.0.0"
description = "Generate ClamAV signatures and YARA rules from malware samples"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.8"
license = {text = "Apache-2.0"}

dependencies = [
    "lief>=0.13.0",
    "pefile>=2023.0.0",
    "click>=8.0.0",
]

[project.scripts]
badsign = "clamav_siggen.cli:main"

[project.urls]
Homepage = "https://github.com/yourusername/badsign"
Documentation = "https://github.com/yourusername/badsign#readme"
Repository = "https://github.com/yourusername/badsign"
```

### 2. Build and Publish

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Test on TestPyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### 3. Install from PyPI

```bash
pip install badsign
```

## Version Control Strategy

### Semantic Versioning

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

Example:
```
1.0.0 - Initial release
1.1.0 - Added YARA generation
1.1.1 - Fixed entropy calculation bug
2.0.0 - Removed deprecated functions
```

### Git Tags

```bash
# Tag releases
git tag -a v1.0.0 -m "Version 1.0.0: Initial standalone release"
git push origin v1.0.0

# Create GitHub release from tag
```

## Maintenance

### Keeping Copies in Sync

If you maintain both the integrated and standalone versions:

```bash
# Option 1: Use git subtree
cd /home/robb/tools/capa-server
git subtree pull --prefix=badsign \
    https://github.com/yourusername/badsign.git main

# Option 2: Use submodule
git submodule add https://github.com/yourusername/badsign.git
git submodule update --remote

# Option 3: Manual sync
rsync -av --delete \
    /home/robb/tools/badsign/ \
    ~/projects/badsign-standalone/
```

### Development Workflow

```bash
# 1. Make changes in standalone repo
cd ~/projects/badsign-standalone
git checkout -b feature/new-capability
# ... make changes ...
git commit -am "Add new feature"
git push origin feature/new-capability

# 2. Create pull request, review, merge

# 3. Update capa-server dependency
cd /home/robb/tools/capa-server
# Update requirements.txt with new version
pip install --upgrade badsign
```

## Testing Standalone Package

### Unit Tests

```bash
cd ~/projects/badsign-standalone

# Run tests
pytest tests/

# With coverage
pytest --cov=clamav_siggen tests/

# Generate HTML coverage report
pytest --cov=clamav_siggen --cov-report=html tests/
```

### Integration Tests

```bash
# Test CLI commands
badsign --help
badsign generate tests/fixtures/malware.exe -o test.ndb
badsign capa-to-yara tests/fixtures/analysis.json -o test.yar

# Test as library
python -c "from clamav_siggen import ClamAVSigGen; print('OK')"
```

### Installation Test

```bash
# Create fresh virtual environment
python -m venv test_env
source test_env/bin/activate

# Install from source
pip install .

# Test command availability
which badsign
badsign --version

# Deactivate and cleanup
deactivate
rm -rf test_env
```

## Summary

### Quick Copy Command

```bash
# One-line copy to new location
cp -r /home/robb/tools/badsign ~/projects/badsign-standalone && \
cd ~/projects/badsign-standalone && \
git init && \
git add . && \
git commit -m "Initial standalone repository"
```

### Key Points

 **Ready to Copy** - No code modifications needed
 **Fully Standalone** - Independent of capa-server
 **Well-Packaged** - Modern Python packaging with pyproject.toml
 **CLI + Library** - Works both ways
 **Tested** - Unit tests included
 **Documented** - Comprehensive README and CLI help
 **Licensed** - Apache 2.0 (same as capa)

### Next Steps

1.  Copy files to new location
2.  Initialize git repository
3.  Test installation and functionality
4.  Create GitHub/GitLab repository
5.  Push code
6.  (Optional) Publish to PyPI
7.  Update capa-server to use as dependency

The package is production-ready and can be separated immediately!
