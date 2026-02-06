# Get the GPU worker pod name
GPU_POD=$(kubectl get pod -l ray.io/group=gpu-group -o jsonpath='{.items[0].metadata.name}')

# Install transformers and torch on GPU worker
kubectl exec $GPU_POD -- pip install transformers torch --break-system-packages

# Also install on head (for completeness)
kubectl exec $HEAD_POD -- pip install transformers torch --break-system-packages

# Deploy the task
kubectl exec $HEAD_POD -- python /tmp/llm-sentiment-analysis.py



#############
# Test it / Demo

# Port-forward the Ray Serve endpoint to your local machine
kubectl port-forward service/raycluster-sample-head-svc 8000:8000 -n default

# Negative sentiment
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Setting up GPU nodes was really frustrating"}'

# Another positive
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "After 18 hours we finally got it working!"}'


# Check if it is consuming GPU
kubectl exec $HEAD_POD -- python -c "
import ray
from ray import serve

ray.init(address='auto')

# Get deployment info
kubectl exec $GPU_POD -- nvidia-smi
kubectl logs $GPU_POD | grep "Loading model"
