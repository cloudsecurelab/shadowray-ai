# shadowray-ai


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
