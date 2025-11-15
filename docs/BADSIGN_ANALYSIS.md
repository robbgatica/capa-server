# ClamAV Signature Generator - Use Case Analysis

**Date:** November 14, 2025
**Context:** Evaluation of building a ClamAV signature generation tool
**Reference:** https://docs.clamav.net/manual/Signatures.html

---

## Executive Summary

Creating a ClamAV signature generator has **significant value**, especially given the existing capa-server infrastructure. The tool would bridge the gap between malware analysis and signature deployment, enabling rapid incident response and lowering the barrier to entry for ClamAV signature writing.

**Recommendation:** Build in phases, starting with hash + string extraction, then integrating with capa-server for capability-based signature generation.

---

##  High-Value Use Cases

### 1. **Integration with capa-server**

You just built capa-server, which identifies malware capabilities. Imagine this workflow:

```
Analyze malware → Detect capabilities → Auto-generate ClamAV signatures
```

For example, if capa detects:
- Unique string patterns (URLs, registry keys, mutexes)
- PE section characteristics
- Specific API call sequences

These could become high-quality ClamAV signatures.

**Example Scenario:**
```
capa detects: "persistence/registry run key" capability
Tool extracts: HKLM\Software\Microsoft\Windows\CurrentVersion\Run\EvilService
Generates: Body signature for registry key string
Result: Signature catches all variants using this persistence mechanism
```

### 2. **Rapid Incident Response**

**Current Workflow:**
1. Analyst finds new malware variant
2. Manually reverse engineers sample
3. Identifies unique patterns
4. Looks up ClamAV signature syntax
5. Writes signature (30-60 minutes)
6. Tests against corpus
7. Deploys across organization

**With Signature Generator:**
1. Analyst uploads sample
2. Tool generates candidate signatures (30 seconds)
3. Analyst validates and deploys (5 minutes)

**Time savings:** 90% reduction in signature creation time

### 3. **YARA-to-ClamAV Bridge**

**Problem:** Many analysts write YARA rules but don't know ClamAV syntax.

**Solution:** Convert existing YARA investment to ClamAV signatures.

**Benefits:**
- Lower barrier to entry
- Leverage existing YARA rule repositories
- Enable dual deployment (YARA for hunting + ClamAV for scanning)
- Reuse community YARA rules as ClamAV signatures

**Example:**
```yara
rule RansomwareNote {
    strings:
        $a = "Your files are encrypted"
        $b = "Send Bitcoin to:"
    condition:
        all of them
}
```

**Converts to:**
```
RansomwareNote.Ransom;Engine:51-255,Target:0;
  (0:596f75722066696c65732061726520656e637279707465640a)&
  (1:53656e6420426974636f696e20746f3a)
```

### 4. **Educational Tool**

Helps analysts learn:
- What makes a good signature (specificity vs. coverage)
- ClamAV syntax and capabilities (hash, body, logical)
- Pattern quality vs. false positive trade-offs
- Signature optimization techniques

**Teaching Features:**
- Explain WHY each pattern was selected
- Show entropy scores for string uniqueness
- Display estimated false positive probability
- Provide signature quality metrics

---

##  Technical Approaches

### **Option A: Pattern Extraction from Analysis**

**Input:** Malware sample + analysis results (capa, strings, PE analysis)
**Output:** Body-based signatures

**Process:**
1. Extract all strings from sample
2. Filter by entropy (remove common strings)
3. Identify unique patterns (compare against known-good corpus)
4. Generate hex patterns from high-value code sections
5. Create logical signatures combining multiple patterns
6. Validate against clean file database

**Advantages:**
- Automated extraction
- Data-driven pattern selection
- Integration with existing analysis tools

**Challenges:**
- Requires clean file corpus for validation
- Pattern quality varies
- May miss semantic/behavioral patterns

### **Option B: YARA to ClamAV Converter**

**Input:** YARA rule
**Output:** ClamAV logical signature

**Example Conversion:**
```yara
rule Malware {
    strings:
        $a = "evil.dll"
        $b = { 90 90 90 90 }
    condition:
        $a and $b
}
```

**Becomes:**
```
Malware.Generic;Engine:51-255,Target:0;
  (0:6576696c2e646c6c)&(1:90909090)
```

**Advantages:**
- Leverage existing YARA rules
- Well-defined input format
- Community rule repositories available

**Challenges:**
- YARA and ClamAV have different capabilities
- Some YARA features can't be converted (PE module, for loop)
- Offset handling differs between formats

### **Option C: Interactive Signature Builder**

**Wizard-style interface:**

1. **Upload malware sample**
2. **Select signature type**
   - Hash-based (MD5/SHA256/PE section hash)
   - Body-based (hex patterns from strings/code)
   - Logical (combination of patterns)
3. **Choose patterns**
   - Tool presents candidate patterns with quality scores
   - Analyst selects/refines patterns
   - Preview signature syntax
4. **Validate against corpus**
   - Test against known-good files
   - Test against known malware families
   - Show false positive/negative rates
5. **Generate + export signature**
   - Output .ndb/.ldb/.yara format
   - Include metadata (date, analyst, description)
   - Optional: Submit to ClamAV community

**Advantages:**
- Human-in-the-loop quality control
- Educational for new analysts
- Flexible workflow

**Challenges:**
- Requires clean/malware corpus
- More manual effort
- UI complexity

---

##  Key Challenges

### **1. False Positives**

**The biggest risk.** A signature that matches legitimate software is worse than no signature.

**Mitigation Strategies:**

**Required:**
- Validation against clean file corpus (minimum 10,000 files)
- Entropy analysis for pattern uniqueness
- Quality scoring system (how specific is this pattern?)
- Test suite (goodware + known malware families)

**Recommended:**
- Integration with VirusTotal (check if pattern matches clean files)
- Whitelist common strings (Windows API names, copyright strings)
- Statistical analysis (pattern frequency in benign vs. malicious)

**Best Practice:**
- Never auto-deploy generated signatures
- Always require human validation
- Provide confidence scores (0-100%)
- Show example matches from validation corpus

### **2. Signature Quality**

**Problem:** Automated signatures might be:
- **Too broad** - Matches benign files (false positives)
- **Too narrow** - Only matches exact sample (easily evaded)
- **Too brittle** - Breaks with minor changes (low coverage)

**Heuristics for Pattern Selection:**

**Good Patterns:**
- High entropy strings (random-looking data)
- Unique error messages
- Malware-specific registry keys
- C2 communication protocols
- Unique PE resource sections

**Bad Patterns:**
- Common API names ("CreateFile", "WriteFile")
- Standard library strings
- Copyright notices
- Generic error messages ("Error", "Failed")
- Common code sequences (function prologues)

**Quality Metrics:**
- **Specificity:** How rare is this pattern? (inverse document frequency)
- **Entropy:** Information content (Shannon entropy > 4.0 is good)
- **Length:** Longer patterns = more specific (min 8 bytes recommended)
- **Stability:** Pattern survives obfuscation/packing?

### **3. ClamAV Format Complexity**

ClamAV supports many signature types, each with different syntax:

**Hash Signatures:**
- MD5: Simple, fast, easily evaded
- SHA1: Better, still evadable
- SHA256: Strong, recommended
- PE Section Hash: Survives some modifications

**Body-based Signatures:**
- Hex patterns with wildcards
- Offset specifications (any, section-based)
- Subsignature combining

**Logical Signatures:**
- Boolean combinations of patterns
- File size conditions
- File type conditions
- PE metadata matching

**Container Signatures:**
- Archives (ZIP, RAR, 7z)
- PDF objects
- Office documents
- Email attachments

**Specialized:**
- YARA integration
- Bytecode signatures (custom C logic)
- Icon signatures (PE icon matching)

**Supporting all would be complex.**

**Recommendation:** Start with hash + body signatures (80% of use cases), expand later.

---

##  Practical Implementation Ideas

### **MVP: Hash + Body Signature Generator**

**Goal:** Deliver value quickly with minimal complexity.

```python
#!/usr/bin/env python3
"""
badsign - Generate ClamAV signatures from malware samples

Usage:
  badsign hash sample.exe
  badsign extract sample.exe --min-length 10 --min-entropy 4.5
  badsign from-capa analysis.json
  badsign validate signature.ndb --corpus /path/to/clean/files

Examples:
  # Generate MD5/SHA256 hash signatures
  badsign hash ransomware.exe > ransomware.hdb

  # Extract unique strings, filter by entropy
  badsign extract trojan.exe --min-entropy 4.5 > trojan.ndb

  # Generate from capa analysis results
  badsign from-capa analysis-123.json > malware.ldb

  # Validate against clean file corpus
  badsign validate signatures.ndb --corpus ~/clean-files/
"""

import hashlib
import pefile
import math
from pathlib import Path

class ClamAVSigGen:
    def __init__(self):
        self.min_entropy = 4.0
        self.min_length = 8
        self.max_length = 1024

    def generate_hash(self, filepath, name="Malware.Generic"):
        """Generate MD5/SHA256 hash signatures"""
        with open(filepath, 'rb') as f:
            data = f.read()

        md5 = hashlib.md5(data).hexdigest()
        sha256 = hashlib.sha256(data).hexdigest()

        # .hdb format: MD5:FileSize:MalwareName
        hdb = f"{md5}:{len(data)}:{name}"

        # .hsb format: SHA256:FileSize:MalwareName
        hsb = f"{sha256}:{len(data)}:{name}"

        return {'hdb': hdb, 'hsb': hsb}

    def calculate_entropy(self, data):
        """Calculate Shannon entropy of data"""
        if not data:
            return 0
        entropy = 0
        for x in range(256):
            p_x = float(data.count(bytes([x]))) / len(data)
            if p_x > 0:
                entropy += - p_x * math.log2(p_x)
        return entropy

    def extract_strings(self, filepath):
        """Extract printable strings with entropy filtering"""
        strings = []
        with open(filepath, 'rb') as f:
            data = f.read()

        # Extract ASCII strings
        current = b''
        for byte in data:
            if 32 <= byte <= 126:  # Printable ASCII
                current += bytes([byte])
            else:
                if len(current) >= self.min_length:
                    entropy = self.calculate_entropy(current)
                    if entropy >= self.min_entropy:
                        strings.append({
                            'string': current.decode('ascii', errors='ignore'),
                            'hex': current.hex(),
                            'entropy': entropy,
                            'length': len(current)
                        })
                current = b''

        # Sort by entropy (highest first)
        strings.sort(key=lambda x: x['entropy'], reverse=True)
        return strings

    def generate_body_signature(self, pattern, name="Malware.Generic"):
        """Generate .ndb body-based signature"""
        # .ndb format: MalwareName:TargetType:Offset:HexSignature
        # TargetType: 0=any, 1=PE, 2=OLE2, etc.
        # Offset: *=any
        return f"{name}:0:*:{pattern}"

    def from_capa_analysis(self, analysis_json):
        """Generate signatures from capa analysis results"""
        import json

        with open(analysis_json) as f:
            data = json.load(f)

        signatures = []

        # Extract patterns from capa capabilities
        for rule_name, rule_data in data.get('rules', {}).items():
            # Look for string matches
            if 'matches' in rule_data:
                for match in rule_data['matches']:
                    # Extract hex patterns from matched strings
                    pass  # Implementation depends on capa JSON structure

        return signatures

    def validate(self, signature, corpus_path):
        """Test signature against clean file corpus"""
        # Run clamscan with signature against corpus
        # Report any matches (potential false positives)
        pass

# Features:
# 1. Hash signatures (trivial but useful)
# 2. String extraction → body signatures
# 3. PE section analysis → targeted signatures
# 4. Validation mode (test against clean files)
```

**Deliverables:**
- Hash signature generation (MD5, SHA256)
- String extraction with entropy filtering
- Body signature generation (.ndb format)
- Basic validation framework

**Effort:** 1-2 weeks
**Value:** High (80% of use cases)

### **Advanced: capa Integration**

**Goal:** Generate capability-specific signatures.

```python
# Leverage capa-server results
# GET /api/analyses/1 → Extract capabilities

def generate_from_capa(analysis_id):
    """Generate signatures based on detected capabilities"""

    # Fetch analysis from capa-server
    response = requests.get(f"http://localhost:8080/api/analyses/{analysis_id}")
    analysis = response.json()
    results = analysis['results']

    signatures = []

    # If capa detects "embed file" capability
    if any('embed file' in rule for rule in results.get('rules', {})):
        # Look for embedded PE/shellcode
        # Extract signatures from embedded artifacts
        signatures.append(extract_embedded_patterns(sample))

    # If capa detects "persistence/registry" capability
    if any('registry' in rule for rule in results.get('rules', {})):
        # Extract registry key patterns
        # Generate signatures for registry persistence
        signatures.append(extract_registry_patterns(sample))

    # If capa detects "network/http" capability
    if any('http' in rule for rule in results.get('rules', {})):
        # Extract URL/domain patterns
        # Generate signatures for C2 communication
        signatures.append(extract_network_patterns(sample))

    # If capa detects "anti-analysis" capability
    if any('anti-analysis' in rule for rule in results.get('rules', {})):
        # Extract anti-debug strings
        # Generate signatures for evasion techniques
        signatures.append(extract_antidebug_patterns(sample))

    return signatures
```

**Deliverables:**
- capa-server API integration
- Capability-to-pattern mapping
- Targeted signature generation
- Quality scoring based on capability confidence

**Effort:** 2-3 weeks
**Value:** Very High (leverages existing analysis)

### **Expert: YARA Converter**

**Goal:** Convert YARA rules to ClamAV logical signatures.

```python
import plyara  # YARA parser

class YARAtoClamAV:
    def __init__(self):
        self.parser = plyara.Plyara()

    def convert(self, yara_rule_text):
        """Convert YARA rule to ClamAV logical signature"""

        # Parse YARA rule
        rules = self.parser.parse_string(yara_rule_text)

        for rule in rules:
            name = rule['rule_name']
            strings = rule.get('strings', [])
            condition = rule.get('condition', '')

            # Convert strings to ClamAV hex patterns
            subsigs = []
            for i, string in enumerate(strings):
                if string['type'] == 'text':
                    hex_pattern = string['value'].encode().hex()
                    subsigs.append(f"({i}:{hex_pattern})")
                elif string['type'] == 'byte':
                    hex_pattern = ''.join(string['value'])
                    subsigs.append(f"({i}:{hex_pattern})")

            # Convert condition to ClamAV logical expression
            # YARA: $a and $b → ClamAV: (0)&(1)
            # YARA: $a or $b → ClamAV: (0)|(1)
            # YARA: 2 of them → More complex...

            clamav_sig = self.build_logical_signature(name, subsigs, condition)
            return clamav_sig

    def build_logical_signature(self, name, subsigs, condition):
        """Build ClamAV .ldb logical signature"""
        # .ldb format:
        # SignatureName;TargetDescriptionBlock;LogicalExpression;Subsig0;Subsig1;...

        # Example: Malware;Engine:51-255,Target:0;(0&1);subsig0;subsig1
        pass

# Handle:
  # - String conditions → hex patterns
  # - Offsets → ClamAV subsignature offsets
  # - File size conditions → logical operators
  # - PE metadata → ClamAV PE signatures
```

**Deliverables:**
- YARA rule parser
- Condition converter (and/or/not)
- String-to-hex converter
- PE metadata handler

**Effort:** 3-4 weeks
**Value:** Very High (enables YARA rule reuse)

---

##  Value Assessment

| Feature | Value | Effort | ROI | Priority |
|---------|-------|--------|-----|----------|
| Hash generator | Low (trivial) | Low | Medium | Quick win  |
| String → Body sig | High | Medium | High | **High**  |
| YARA converter | Very High | High | High | **High**  |
| capa integration | High | Medium | Very High | **High**  |
| PE section analysis | High | Medium | High | Medium |
| Validation framework | Critical | Medium | Critical | **High**  |
| Logical sig builder | Medium | High | Low | Low |
| Container sigs | Low | Very High | Very Low | Low |
| Interactive UI | Medium | High | Medium | Medium |

**Legend:**
-  = Implement first (foundation)
-  = High priority (core value)

---

##  Recommended Phased Approach

### **Phase 1: Foundation (1-2 weeks)**

**Goal:** Deliver functional MVP

**Features:**
1.  Hash signature generator (MD5, SHA256, PE section)
2.  String extraction with entropy filtering
3.  Basic body signature generation (.ndb format)
4.  Validation against known-good corpus
5.  CLI interface

**Deliverables:**
- `badsign` command-line tool
- Basic documentation
- Example signatures

**Testing:**
- 100 malware samples
- 10,000 clean files
- Measure false positive rate (target: <0.1%)

### **Phase 2: Integration (2-3 weeks)**

**Goal:** Integrate with existing tools

**Features:**
5.  capa-server integration
   - Parse capa JSON results
   - Extract patterns from detected capabilities
   - Generate capability-specific signatures
6.  PE/ELF structure analysis
   - Section hash signatures
   - Import table patterns
   - Resource section patterns
7.  Quality scoring system
   - Entropy-based scoring
   - Corpus frequency analysis
   - Confidence ratings (0-100%)

**Deliverables:**
- `/api/generate-signature` endpoint in capa-server
- One-click signature generation from web UI
- Signature quality dashboard

**Testing:**
- Integration tests with capa-server
- Quality score validation
- Performance benchmarks

### **Phase 3: Advanced (3-4 weeks)**

**Goal:** Enable advanced workflows

**Features:**
8.  YARA to ClamAV converter
   - Parse YARA syntax
   - Convert conditions to logical expressions
   - Handle offsets and metadata
9.  Logical signature builder
   - Combine multiple patterns
   - Boolean logic (AND/OR/NOT)
   - File size/type conditions
10.  Signature optimization
    - Wildcard placement
    - Subsignature extraction
    - Performance tuning

**Deliverables:**
- YARA converter tool
- Logical signature wizard
- Optimization recommendations

**Testing:**
- Convert 100 YARA rules
- Validate converted signatures
- Performance comparison

---

##  Integration with Existing Tools

### **capa-server Integration Vision**

Since you have **capa-server**, the integration workflow would be:

```
┌─────────────────────────────────────────────────────────────┐
│  1. Upload malware → capa-server analyzes                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│  2. Analysis completes:                                      │
│     - Detected 15 capabilities                               │
│     - Mapped to ATT&CK techniques                            │
│     - Extracted strings, API calls, etc.                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│  3. Click "Generate ClamAV Signature" button                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│  4. Signature Generator:                                     │
│     - Extracts unique strings from capabilities              │
│     - Analyzes PE characteristics                            │
│     - Identifies network indicators                          │
│     - Calculates entropy/uniqueness scores                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│  5. Validation:                                              │
│     - Tests against clean file database (10,000 files)       │
│     - No matches = Good signature                           │
│     - Matches found = False positive warning                │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│  6. Output:                                                  │
│     - Ready-to-use .ndb/.ldb/.hsb signature                  │
│     - Quality score (0-100%)                                 │
│     - Explanation of what each pattern detects              │
│     - Optional: Auto-test against VirusTotal                 │
└──────────────────────────────────────────────────────────────┘
```

### **Example UI Flow**

**In capa-server web interface:**

```
┌─────────────────────────────────────────────────────────┐
│ Analysis #123: ransomware.exe                           │
├─────────────────────────────────────────────────────────┤
│ Status: Completed                                      │
│ Capabilities: 18 detected                               │
│ ATT&CK: T1486, T1027, T1490, ...                       │
├─────────────────────────────────────────────────────────┤
│ Actions:                                                │
│  [View Results]  [Download JSON]  [Generate Signature]  │
└─────────────────────────────────────────────────────────┘
```

**Click "Generate Signature" →**

```
┌─────────────────────────────────────────────────────────┐
│ ClamAV Signature Generator                              │
├─────────────────────────────────────────────────────────┤
│ Analyzing sample...                                     │
│   Extracted 245 strings                               │
│   Filtered to 12 high-entropy patterns                │
│   Identified 3 unique API call sequences              │
│   Validated against 10,000 clean files                │
│   No false positives detected                         │
├─────────────────────────────────────────────────────────┤
│ Generated Signatures:                                   │
│                                                         │
│ 1. Hash Signature (SHA256)                             │
│    Quality: 100% | Evasion: Easy                       │
│    [Copy] [Download]                                   │
│                                                         │
│ 2. Ransom Note String                                  │
│    Pattern: "Your files are encrypted..."              │
│    Quality: 95% | Evasion: Medium                      │
│    [Copy] [Download]                                   │
│                                                         │
│ 3. Persistence Registry Key                            │
│    Pattern: HKLM\...\RansomService                     │
│    Quality: 90% | Evasion: Hard                        │
│    [Copy] [Download]                                   │
│                                                         │
│ 4. Logical Signature (Combined)                        │
│    Combines patterns 2 & 3 with file size check        │
│    Quality: 98% | Evasion: Very Hard                   │
│    [Copy] [Download]                                   │
├─────────────────────────────────────────────────────────┤
│ [Download All Signatures] [Test with clamscan]         │
└─────────────────────────────────────────────────────────┘
```

### **API Endpoint Design**

```python
# New endpoint in capa-server
@app.post("/api/analyses/{analysis_id}/generate-signature")
async def generate_clamav_signature(
    analysis_id: int,
    signature_type: str = "auto",  # auto, hash, body, logical
    validate: bool = True,
    db: Session = Depends(get_db)
):
    """
    Generate ClamAV signature from analysis results.

    Returns:
    {
        "signatures": [
            {
                "type": "hash",
                "format": "hsb",
                "signature": "abc123...:12345:Ransomware.Generic",
                "quality_score": 100,
                "false_positive_risk": "low",
                "description": "SHA256 hash of entire file"
            },
            {
                "type": "body",
                "format": "ndb",
                "signature": "Ransomware.Note:0:*:596f75722066696c6573...",
                "quality_score": 95,
                "false_positive_risk": "low",
                "description": "Ransom note text pattern"
            }
        ],
        "validation": {
            "tested_files": 10000,
            "false_positives": 0,
            "confidence": "high"
        }
    }
    """
```

---

##  My Opinion & Recommendation

### **YES, there's significant value**, especially if you:

1. **Focus on quality over quantity**
   - One good signature > 100 bad ones
   - Always validate against clean corpus
   - Provide quality metrics and confidence scores

2. **Integrate with capa**
   - Leverage capability detection for smarter patterns
   - Map capabilities to signature strategies
   - Generate targeted, context-aware signatures

3. **Prioritize validation**
   - False positives kill adoption
   - Build comprehensive test framework
   - Make validation results transparent

4. **Make it educational**
   - Show WHY a pattern is good
   - Explain entropy, uniqueness, evasion resistance
   - Help analysts learn signature craft

5. **Start simple**
   - Hash + string extraction gets 80% value with 20% effort
   - Add complexity incrementally
   - Validate each phase before moving forward

### **The Killer Feature**

**"One-click: malware → capa analysis → validated ClamAV signature"**

This would be genuinely useful for:
- **SOC teams** - Rapid response to new threats
- **Malware analysts** - Automated documentation and IOC generation
- **Researchers** - Scalable signature generation for large corpuses
- **ClamAV rule writers** - Modern tooling for an underserved area

### **Unique Value Proposition**

**No existing tool does this well:**
- **Manual signature writing** - Time-consuming, requires expertise
- **YARA** - Different syntax, not all rules convert
- **Commercial AV** - Closed-source, proprietary signatures
- **capa** - Detects capabilities but doesn't generate signatures

**Your tool would:**
- Bridge the gap between analysis and detection
- Democratize ClamAV signature creation
- Integrate with modern analysis workflows
- Focus on quality and validation

### **Next Steps**

**If you decide to build this, I'd recommend:**

1. **Week 1:** Build hash + string extractor MVP
2. **Week 2:** Add entropy filtering and validation
3. **Week 3:** Integrate with capa-server API
4. **Week 4:** Add web UI to capa-server
5. **Review:** Test with real samples, gather feedback

**Then decide:**
- YARA converter? (if community wants it)
- Logical signature builder? (if advanced users need it)
- VirusTotal integration? (if validation corpus insufficient)

---

##  References

### **ClamAV Documentation**
- Signature formats: https://docs.clamav.net/manual/Signatures.html
- Signature writing guide: https://docs.clamav.net/manual/Signatures/ExtendedSignatures.html
- Testing: https://docs.clamav.net/manual/Usage/Scanning.html

### **Related Tools**
- **YARA:** https://virustotal.github.io/yara/
- **plyara:** YARA parser - https://github.com/plyara/plyara
- **capa:** Capability detection - https://github.com/mandiant/capa
- **pefile:** PE parser - https://github.com/erocarrera/pefile

### **Research**
- "Automatic Signature Generation for Malware Detection" (various papers)
- MITRE ATT&CK Framework: https://attack.mitre.org/
- ClamAV signature database: https://www.clamav.net/downloads

---

##  Appendix: Example Signature Formats

### **Hash-based Signature (.hdb - MD5)**
```
# Format: MD5:FileSize:MalwareName
d41d8cd98f00b204e9800998ecf8427e:68:Malware.Generic
```

### **Hash-based Signature (.hsb - SHA256)**
```
# Format: SHA256:FileSize:MalwareName
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855:68:Malware.Generic
```

### **Body-based Signature (.ndb)**
```
# Format: MalwareName:TargetType:Offset:HexSignature
Ransomware.Note:0:*:596f75722066696c65732061726520656e637279707465640a
#                    "Your files are encrypted\n" in hex
```

### **Logical Signature (.ldb)**
```
# Format: Name;TargetDescriptionBlock;LogicalExpression;Subsig0;Subsig1;...
Ransomware.Multi;Engine:51-255,Target:0;(0&1);
  596f75722066696c65732061726520656e637279707465640a;
  53656e6420426974636f696e20746f3a

# Matches if BOTH patterns found:
#   Pattern 0: "Your files are encrypted"
#   Pattern 1: "Send Bitcoin to:"
```

### **PE Section Hash (.mdb)**
```
# Format: PESection:SectionHash:FileSize:MalwareName
.text:d41d8cd98f00b204e9800998ecf8427e:*:Trojan.Packed
```

### **Icon Signature (.idb)**
```
# Format: IconGroupID:IconHash:MalwareName
1:d41d8cd98f00b204e9800998ecf8427e:Malware.FakeAV
```

---

**End of Analysis**

**Conclusion:** Building a ClamAV signature generator is a high-value project that complements your existing capa-server infrastructure. Start with an MVP focused on hash and body signatures, integrate with capa for capability-based generation, and expand to YARA conversion based on user demand.

**Estimated Total Effort:** 6-10 weeks for full implementation
**Estimated Value:** Very High - fills a significant gap in malware analysis workflows

**Decision Point:** Would you like to proceed with a prototype or explore specific implementation details?
