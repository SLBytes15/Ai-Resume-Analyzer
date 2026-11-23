import asyncio

# Shared semaphore to strictly serialize local Ollama inference on Apple M2 (8GB RAM)
# Configured with concurrency limit of 1 to prevent swap thrashing and host memory exhaustion
ollama_inference_semaphore = asyncio.Semaphore(1)
