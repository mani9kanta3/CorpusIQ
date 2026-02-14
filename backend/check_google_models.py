"""Quick script to check available Google embedding models."""

import os
from google import genai

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Set GOOGLE_API_KEY first")
    exit()

client = genai.Client(api_key=api_key)

print("Available models that support embedContent:")
print("=" * 50)

for model in client.models.list():
    model_name = model.name
    # Check if model supports embedding
    supported_methods = model.supported_actions if hasattr(model, 'supported_actions') else []
    
    if 'embed' in model_name.lower() or 'embedding' in model_name.lower():
        print(f"  {model_name}")