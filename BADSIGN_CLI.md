# badsign - Standalone CLI Usage Guide

> **Generating signatures for bad stuff, period.**

`badsign` is a standalone command-line tool for generating malware signatures. It can be used independently of capa-server for signature generation workflows.

## Two Modes of Operation

| Mode | Input Required | Output | Commands |
|------|---------------|---------|----------|
| **Binary Analysis** | Malware file only | ClamAV signatures (hash, strings, PE sections) | `generate`, `hash`, `extract` |
| **Behavioral Analysis** | capa JSON results | YARA rules + enhanced signatures | `capa-to-yara`, `from-capa` |

**Important:** ClamAV signatures can be generated directly from malware binaries. YARA behavioral rules require running capa analysis first.

## Installation

### From Source (Recommended)

```bash
# Clone the repository
git clone /home/robb/tools/badsign
cd badsign

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Verify installation
badsign --version
```

### System Requirements

- Python 3.8+
- LIEF library (cross-platform binary parsing)
- Optional: ClamAV installed for signature testing

## Available Commands

```
badsign [OPTIONS] COMMAND [ARGS]...

Commands:
  capa-to-yara  Generate YARA rule from capa analysis results
  extract       Extract unique strings from malware sample
  from-capa     Generate ClamAV signatures from capa analysis results
  generate      Generate all signature types for a malware sample
  hash          Generate hash-based signatures
  validate      Validate signatures against clean file corpus
```

## Command Reference

### 1. generate - Generate All Signature Types

Generate hash, body, and section signatures from a malware sample.

**Syntax:**
```bash
badsign generate [OPTIONS] FILE_PATH
```

**Options:**
- `--name TEXT` - Malware name for signatures (default: filename)
- `--string-count INTEGER` - Number of string signatures to generate (default: 10)
- `-o, --output PATH` - Output file (default: stdout)

**Examples:**

```bash
# Generate all signatures for a malware sample
badsign generate malware.exe --name "TrojanBanker" -o banker.ndb

# Generate with more string signatures
badsign generate malware.exe --string-count 20 -o sigs.ndb

# Output to stdout
badsign generate malware.exe --name "Backdoor"
```

**Output Format:**

The `.ndb` file contains:
1. **Hash signatures** - MD5 and SHA256 file hashes
2. **Body signatures** - Hex patterns from unique strings
3. **PE section hashes** - Section-specific signatures (PE files only)

### 2. capa-to-yara - Generate YARA from capa Analysis

Create behavioral YARA rules from capa malware capability analysis.

**Syntax:**
```bash
badsign capa-to-yara [OPTIONS] CAPA_JSON
```

**Options:**
- `-o, --output PATH` - Output YARA rule file (.yar) **[required]**
- `--name TEXT` - Custom rule name (auto-generated if not provided)
- `--min-confidence [low|medium|high]` - Minimum confidence level (default: medium)
- `--min-capabilities INTEGER` - Minimum capabilities required (default: 2)

**Examples:**

```bash
# Step 1: Analyze malware with capa
capa malware.exe --json > analysis.json

# Step 2: Generate YARA rule from capabilities
badsign capa-to-yara analysis.json -o behavior.yar

# Generate with high confidence only
badsign capa-to-yara analysis.json -o rule.yar \
    --min-confidence high \
    --min-capabilities 3

# Custom rule name
badsign capa-to-yara analysis.json -o rule.yar \
    --name "APT_TrojanLoader_2024"
```

**Generated YARA Features:**

- Automatic malware categorization (Ransomware, Trojan, Backdoor, etc.)
- Cross-platform support (PE, ELF, Mach-O detection)
- MITRE ATT&CK technique mapping
- API call and capability strings
- Confidence-based rule conditions

**Example Output:**

```yara
rule Win64_Backdoor_Generic {
    meta:
        description = "Detects backdoor based on behavioral capabilities"
        generated_from = "capa analysis"
        date = "2025-11-15"
        mitre_attack = "T1033, T1059.003, T1087, T1129"
        confidence = "high"

    strings:
        $api_1 = "CreateThread" ascii
        $api_2 = "VirtualProtect" ascii
        // ... more capability strings

    condition:
        uint16(0) == 0x5A4D and
        filesize < 10MB and
        (any of ($api_*))
}
```

### 3. from-capa - Generate ClamAV from capa Analysis

Generate ClamAV signatures based on capa analysis results (not just raw binary).

**Syntax:**
```bash
badsign from-capa [OPTIONS] CAPA_JSON
```

**Options:**
- `--name TEXT` - Malware name prefix
- `-o, --output PATH` - Output file (default: stdout)

**Examples:**

```bash
# Analyze with capa, generate ClamAV sigs
capa malware.exe --json > analysis.json
badsign from-capa analysis.json --name "Backdoor" -o sigs.ndb
```

### 4. hash - Generate Hash Signatures

Generate only hash-based signatures (MD5, SHA256, section hashes).

**Syntax:**
```bash
badsign hash [OPTIONS] FILE_PATH
```

**Examples:**

```bash
# Generate hash signatures
badsign hash malware.exe

# Save to file
badsign hash malware.exe -o hashes.txt
```

### 5. extract - Extract Strings

Extract unique strings from malware with entropy filtering.

**Syntax:**
```bash
badsign extract [OPTIONS] FILE_PATH
```

**Options:**
- `--min-entropy FLOAT` - Minimum entropy threshold (default: 4.0)
- `--min-length INTEGER` - Minimum string length (default: 8)
- `--max-strings INTEGER` - Maximum number of strings (default: 100)

**Examples:**

```bash
# Extract high-entropy strings
badsign extract malware.exe --min-entropy 4.5

# Extract with custom filters
badsign extract malware.exe \
    --min-entropy 3.5 \
    --min-length 10 \
    --max-strings 50
```

### 6. validate - Validate Signatures

Test signatures against a corpus of clean files to check for false positives.

**Syntax:**
```bash
badsign validate [OPTIONS] SIGNATURE_FILE
```

**Options:**
- `--corpus PATH` - Path to clean file corpus directory

**Examples:**

```bash
# Validate against clean files
badsign validate malware.ndb --corpus /path/to/clean/files
```

## Complete Workflow Examples

### Workflow 1: Malware Analysis → YARA Rule

```bash
# 1. Analyze malware with capa
capa suspicious.exe --json > analysis.json

# 2. Generate behavioral YARA rule
badsign capa-to-yara analysis.json -o detection.yar \
    --min-confidence medium \
    --min-capabilities 2

# 3. Test the YARA rule
yara detection.yar /malware_samples/

# 4. Use in production
sudo cp detection.yar /var/lib/yara/rules/
```

### Workflow 2: Malware Analysis → ClamAV Signatures

```bash
# 1. Analyze malware with capa (for context)
capa trojan.exe --json > analysis.json

# 2. Generate all ClamAV signature types
badsign generate trojan.exe --name "TrojanBanker" -o sigs.ndb

# 3. Extract specific signature types
grep -E "^[0-9a-f]{32}:" sigs.ndb > banker.hdb    # MD5
grep -E "^[0-9a-f]{64}:" sigs.ndb > banker.hsb    # SHA256
grep "^TrojanBanker\." sigs.ndb > banker.ndb      # Body sigs

# 4. Test with ClamAV
clamscan -d banker.hdb suspicious_file.exe
clamscan -d banker.ndb suspicious_file.exe

# 5. Deploy to ClamAV (requires root)
sudo cp banker.hdb /var/lib/clamav/
sudo cp banker.ndb /var/lib/clamav/
sudo systemctl reload clamav-daemon
```

### Workflow 3: String Extraction → Manual Signature Creation

```bash
# 1. Extract high-quality strings
badsign extract malware.exe --min-entropy 4.5 > strings.txt

# 2. Review and select unique strings
cat strings.txt

# 3. Generate signatures from selected strings
# (Use the generate command with the original binary)
badsign generate malware.exe --string-count 5 -o custom.ndb
```

## Using with ClamAV

### Extract Signature Types

The combined `.ndb` file needs to be split for ClamAV:

```bash
# Download/generate combined file
badsign generate malware.exe -o combined.ndb

# Extract MD5 hash signatures (.hdb format)
grep -E "^[0-9a-f]{32}:" combined.ndb > malware.hdb

# Extract SHA256 signatures (.hsb format)
grep -E "^[0-9a-f]{64}:" combined.ndb > malware.hsb

# Extract body signatures (.ndb format)
grep "^[A-Za-z].*:0:\*:" combined.ndb > malware.ndb

# Extract PE section hashes (.mdb format)
grep "^\." combined.ndb > malware.mdb
```

### Test Signatures

```bash
# Test individual signature files
clamscan -d malware.hdb test_file.exe
clamscan -d malware.ndb test_file.exe
clamscan -d malware.mdb test_file.exe

# Test directory with all signatures
clamscan -d malware.hdb -d malware.ndb -r /suspect_files/
```

### Deploy Signatures

```bash
# Copy to ClamAV database directory (requires root)
sudo cp malware.hdb /var/lib/clamav/
sudo cp malware.hsb /var/lib/clamav/
sudo cp malware.ndb /var/lib/clamav/

# Reload ClamAV daemon
sudo systemctl reload clamav-daemon

# Or restart if reload doesn't work
sudo systemctl restart clamav-daemon

# Verify signatures are loaded
sudo clamdscan --version
```

## Python Library Usage

You can also use `badsign` as a Python library:

```python
from clamav_siggen import ClamAVSigGen
from clamav_siggen.capa_parser import CapaParser
from clamav_siggen.yara_generator import YaraGenerator
import json

# Example 1: Generate all signature types
siggen = ClamAVSigGen(file_path="malware.exe")

# Generate hash signatures
hash_sigs = siggen.generate_hash_signatures(name="Malware")
print(hash_sigs['hdb'])  # MD5 signature
print(hash_sigs['hsb'])  # SHA256 signature

# Extract strings with entropy filtering
strings = siggen.extract_strings(min_entropy=4.5, min_length=10)
print(f"Found {len(strings)} high-quality strings")

# Generate body signatures
body_sigs = siggen.generate_body_signatures(
    strings=strings[:10],
    name="Malware"
)

# Generate all signatures at once
all_sigs = siggen.generate_all(
    name="MyMalware",
    include_strings=True,
    string_count=10
)

# Example 2: YARA from capa analysis
with open('analysis.json', 'r') as f:
    capa_data = json.load(f)

parser = CapaParser(capa_dict=capa_data)
generator = YaraGenerator(parser)

yara_rule = generator.generate_rule(
    rule_name="CustomMalware",
    min_capabilities=2,
    min_confidence="medium"
)

print(yara_rule)
```

## Standalone Repository Structure

To copy `badsign` to a separate repository, include these files:

```
badsign/
├── clamav_siggen/           # Main package
│   ├── __init__.py
│   ├── core.py              # ClamAVSigGen class
│   ├── capa_parser.py       # capa JSON parser
│   ├── yara_generator.py    # YARA rule generation
│   ├── cli.py               # CLI interface
│   └── utils.py             # Utilities
├── tests/                   # Unit tests
├── examples/                # Example files
├── docs/                    # Documentation
├── requirements.txt         # Dependencies
├── requirements-dev.txt     # Dev dependencies
├── pyproject.toml          # Package metadata
├── setup.py                # Installation script
├── README.md               # Main documentation
└── LICENSE                 # Apache 2.0 license
```

**Key Dependencies** (from requirements.txt):
```
lief>=0.13.0        # Binary parsing
pefile>=2023.0.0    # PE file analysis
click>=8.0.0        # CLI framework
```

**Repository URL:** `/home/robb/tools/badsign/`

## Tips and Best Practices

### String Selection

- Use `--min-entropy 4.5` or higher for unique patterns
- Avoid common strings like "Program Files" or "Windows"
- Review extracted strings manually before deployment

### YARA Rules

- Use `--min-confidence medium` or `high` for production
- Test rules against clean file corpus first
- Adjust `--min-capabilities` based on desired specificity

### ClamAV Signatures

- Hash signatures are most reliable but easily evaded
- Body signatures provide better detection but may have false positives
- Section hashes work well for PE malware families
- Always test against known clean files

### Performance

- Extract signatures from representative samples
- Use fewer body signatures for faster scanning
- Combine multiple signature types for defense in depth

## Troubleshooting

### Command not found

```bash
# Ensure badsign is installed
pip list | grep badsign

# Reinstall if needed
cd /home/robb/tools/badsign
pip install -e .
```

### LIEF parsing errors

```bash
# Update LIEF
pip install --upgrade lief

# Some files may not be supported (corrupted, packed, etc.)
```

### False positives

```bash
# Test against clean corpus
badsign validate signatures.ndb --corpus /usr/bin/

# Increase entropy threshold
badsign extract malware.exe --min-entropy 5.0

# Reduce number of body signatures
badsign generate malware.exe --string-count 5
```

## Additional Resources

- [ClamAV Signature Documentation](https://docs.clamav.net/manual/Signatures.html)
- [capa Documentation](https://github.com/mandiant/capa)
- [YARA Documentation](https://virustotal.github.io/yara/)
- [LIEF Documentation](https://lief.quarkslab.com/)

## Support

For issues with `badsign`:
- Check the README.md in `/home/robb/tools/badsign/`
- Review example files in `/home/robb/tools/badsign/examples/`
- See implementation details in `PROJECT_STATUS.md`

For issues with capa-server integration:
- See capa-server README.md
- Check API documentation at `http://localhost:8080/docs`
