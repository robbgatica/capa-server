# Quick Start: YARA Rule Generation

**5-minute guide to test the capa-server YARA integration**

---

## Prerequisites

- Docker or Podman installed
- Both directories present:
  - `~/tools/capa-server/`
  - `~/tools/badsign/`

---

## Step 1: Build Container (2 minutes)

```bash
cd ~/tools/capa-server

# Build the container (includes badsign)
podman-compose build

# Or with Docker:
# docker-compose build
```

**What happens:**
- Container built from parent directory context
- badsign installed from local package
- capa-server application copied
- YARA generation enabled

---

## Step 2: Start Server (30 seconds)

```bash
# Start the container
podman-compose up -d

# Check logs
podman-compose logs -f

# Wait for: "Application startup complete"
# Press Ctrl+C to exit logs
```

**Verify it's running:**
```bash
curl http://localhost:8080/health

# Should return: {"status":"healthy","version":"0.1.0"}
```

---

## Step 3: Verify YARA Integration (10 seconds)

```bash
curl http://localhost:8080/api/info

# Look for: "yara_generation_available": true
```

**Expected output:**
```json
{
  "name": "capa-server",
  "version": "0.1.0",
  "capa_rules_count": 1234,
  "max_file_size_mb": 100,
  "yara_generation_available": true  ← This should be true!
}
```

---

## Step 4: Upload Test Sample (30 seconds)

**Option A: Use existing malware sample**
```bash
# If you have a sample from theZoo
curl -X POST -F "file=@~/tools/theZoo/live/FancyBear.GermanParliament" \
  http://localhost:8080/api/analyze

# Note the analysis_id from response
```

**Option B: Create a simple test binary**
```bash
# Create a simple ELF binary
echo -e '#!/bin/bash\necho "test"' > /tmp/test.sh
chmod +x /tmp/test.sh

# Upload it
curl -X POST -F "file=@/tmp/test.sh" \
  http://localhost:8080/api/analyze
```

**Response:**
```json
{
  "message": "Analysis started",
  "analysis_id": 1,
  "duplicate": false
}
```

---

## Step 5: Wait for Analysis (10-60 seconds)

```bash
# Check status (replace 1 with your analysis_id)
curl http://localhost:8080/api/analyses/1 | jq .status

# Keep checking until you see: "completed"
# Or watch in real-time:
watch -n 2 'curl -s http://localhost:8080/api/analyses/1 | jq .status'
```

---

## Step 6: Generate YARA Rule (5 seconds)

```bash
# Generate YARA rule
curl -X POST "http://localhost:8080/api/analyses/1/generate-yara" \
  --output test.yar

# View the generated rule
cat test.yar
```

**You should see a YARA rule like:**
```yara
rule Win64_Trojan_Generic {
    meta:
        description = "Detects trojan based on behavioral capabilities"
        generated_from = "capa analysis"
        ...

    strings:
        $str_1 = "some_string" ascii
        $api_1 = "CreateProcess" ascii
        ...

    condition:
        uint16(0) == 0x5A4D and
        filesize < 10MB and
        ...
}
```

---

## Step 7: Test YARA Rule (10 seconds)

```bash
# Test the rule against the original sample
# (You need YARA installed on your host)

yara test.yar ~/tools/theZoo/live/FancyBear.GermanParliament

# Expected: Rule name printed if it matches
```

---

## Step 8: Test Web UI (30 seconds)

1. **Open browser:** http://localhost:8080/
2. **Upload a file** (drag & drop or click to browse)
3. **Wait for analysis to complete** (status will change from "pending" → "processing" → "completed")
4. **Click "Generate YARA"** button (green button)
5. **Download the .yar file** automatically

---

## Complete Test Script

Save this as `test_yara_integration.sh`:

```bash
#!/bin/bash

echo "=== YARA Integration Test ==="

# 1. Check if server is running
echo -e "\n[1/6] Checking server health..."
curl -s http://localhost:8080/health | jq .

# 2. Verify YARA generation available
echo -e "\n[2/6] Verifying YARA integration..."
curl -s http://localhost:8080/api/info | jq .yara_generation_available

# 3. Upload test sample (using a simple script)
echo -e "\n[3/6] Creating and uploading test sample..."
echo -e '#!/bin/bash\necho "test"' > /tmp/test_sample.sh
chmod +x /tmp/test_sample.sh

RESPONSE=$(curl -s -X POST -F "file=@/tmp/test_sample.sh" http://localhost:8080/api/analyze)
ANALYSIS_ID=$(echo $RESPONSE | jq -r .analysis_id)
echo "Analysis ID: $ANALYSIS_ID"

# 4. Wait for completion
echo -e "\n[4/6] Waiting for analysis to complete..."
for i in {1..30}; do
  STATUS=$(curl -s http://localhost:8080/api/analyses/$ANALYSIS_ID | jq -r .status)
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ]; then
    break
  fi
  sleep 2
done

# 5. Generate YARA rule
echo -e "\n[5/6] Generating YARA rule..."
curl -s -X POST "http://localhost:8080/api/analyses/$ANALYSIS_ID/generate-yara" \
  --output /tmp/test_yara_$ANALYSIS_ID.yar

# 6. Display rule
echo -e "\n[6/6] Generated YARA rule:"
cat /tmp/test_yara_$ANALYSIS_ID.yar

echo -e "\n=== Test Complete ==="
echo "YARA rule saved to: /tmp/test_yara_$ANALYSIS_ID.yar"
```

**Run it:**
```bash
chmod +x test_yara_integration.sh
./test_yara_integration.sh
```

---

## Troubleshooting

### Container won't build
**Error:** "COPY failed: file not found: badsign/"

**Fix:**
```bash
# Make sure you're in the right directory
cd ~/tools/capa-server

# Check that badsign exists in parent directory
ls -la ../badsign/

# Rebuild
podman-compose build --no-cache
```

### YARA generation not available
**Check:** `"yara_generation_available": false`

**Fix:**
```bash
# Check if badsign is installed in container
podman exec capa-server pip list | grep badsign

# If not found, rebuild container
podman-compose down
podman-compose build --no-cache
podman-compose up -d
```

### Analysis stuck in "processing"
**Fix:**
```bash
# Check container logs
podman-compose logs -f

# Look for errors like:
# - "capa command failed"
# - "UnsupportedFormatError"
# - "Analysis timed out"
```

### Permission denied errors
**Fix:**
```bash
# Fix data directory permissions
chmod -R 777 ~/tools/capa-server/data/

# Restart container
podman-compose restart
```

---

## Next Steps

Once you've verified the integration works:

1. **Read full documentation:** `YARA_INTEGRATION.md`
2. **Test with real malware:** Upload samples from theZoo
3. **Experiment with parameters:**
   - Try `min_confidence=low` vs `high`
   - Adjust `min_capabilities` (1, 2, 3, etc.)
4. **Compare YARA rules:** See how rules differ for different malware families
5. **Deploy in production:** Integrate with your malware analysis workflow

---

## Success Criteria

 Server responds to `/health`
 `/api/info` shows `"yara_generation_available": true`
 Can upload a sample and get analysis_id
 Analysis completes successfully
 YARA rule is generated and downloaded
 YARA rule is valid syntax
 Web UI shows "Generate YARA" button

---

**If all checks pass:** Integration is working! 

**Questions?** See `YARA_INTEGRATION.md` for detailed documentation.
