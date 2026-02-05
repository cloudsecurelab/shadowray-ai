# llm_serve_demo.py
from ray import serve
from starlette.requests import Request
import ray

# Initialize Ray (connect to existing cluster)
ray.init(address="auto")

@serve.deployment(
    route_prefix="/analyze",
    num_replicas=2,
    ray_actor_options={"num_cpus": 0.5}
)
class SentimentAnalyzer:
    def __init__(self):
        # Using transformers for sentiment analysis
        from transformers import pipeline
        print("Loading sentiment analysis model...")
        self.model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1  # CPU only
        )
        print("Model loaded successfully!")
    
    async def __call__(self, request: Request):
        data = await request.json()
        text = data.get("text", "")
        
        if not text:
            return {"error": "No text provided"}
        
        # Run inference
        result = self.model(text)[0]
        
        return {
            "text": text,
            "sentiment": result["label"],
            "confidence": round(result["score"], 4)
        }

# Deploy the service
serve.run(SentimentAnalyzer.bind(), name="sentiment_service")

print("✅ Sentiment Analysis Service is running!")
print("📍 Endpoint: http://<ray-head-ip>:8000/analyze")
