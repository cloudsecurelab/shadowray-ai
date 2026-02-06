# llm_serve_demo_gpu.py
from ray import serve
from starlette.requests import Request
import ray

# Initialize Ray
ray.init(address="auto")

@serve.deployment(
    route_prefix="/analyze",
    num_replicas=1,
    ray_actor_options={
        "num_cpus": 1,
        "num_gpus": 1
    }
)
class SentimentAnalyzer:
    def __init__(self):
        from transformers import pipeline
        import torch
        
        device = 0 if torch.cuda.is_available() else -1
        device_name = "GPU" if device == 0 else "CPU"
        
        print(f"🚀 Loading model on {device_name}...")
        self.model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=device
        )
        print(f"✅ Model loaded on {device_name}!")
    
    async def __call__(self, request: Request):
        data = await request.json()
        text = data.get("text", "")
        
        if not text:
            return {"error": "No text provided"}
        
        result = self.model(text)[0]
        
        return {
            "text": text,
            "sentiment": result["label"],
            "confidence": round(result["score"], 4)
        }

serve.run(SentimentAnalyzer.bind(), name="sentiment_service")
print("✅ Sentiment Analysis Service running on GPU!")
