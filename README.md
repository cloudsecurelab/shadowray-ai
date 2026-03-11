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

## Test with the Python UI using venv
python3 -m venv venv
source venv/bin/activate
pip install gradio requests
python inference/frontend.py

-

# Quick Start Day-2 

### Port-forward the Ray Serve endpoint to your local machine
kubectl port-forward service/raycluster-sample-head-svc 8000:8000 -n default

## Expose the Ray Dashboard (to accept job submissions)
kubectl port-forward svc/raycluster-sample-head-svc 8265:8265

## Test with the Python UI using venv
python3 -m venv venv
source venv/bin/activate
pip install gradio requests
python inference/frontend.py

-
