#!/usr/bin/env python3
"""Test Ollama embeddings API"""
import requests
import json

print("Testing Ollama embeddings...")

try:
    response = requests.post(
        "http://127.0.0.1:11434/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": "hello"},
        timeout=120
    )
    
    data = response.json()
    embedding = data.get("embedding", [])
    print(f"✅ Success!")
    print(f"Embedding dims: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
except Exception as e:
    print(f"❌ Error: {e}")
