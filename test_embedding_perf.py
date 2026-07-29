"""
Benchmark for EmbeddingService lazy loading optimization.
"""
import sys
import os
import time
import threading
import logging

sys.path.insert(0, os.getcwd())
from dotenv import load_dotenv
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

from ai_pipeline.embeddings.embedding_service import EmbeddingService

def run_embedding(worker_id: int, results: dict):
    print(f"\n[Worker {worker_id}] Starting embedding request...")
    start = time.time()
    service = EmbeddingService()
    # Dummy texts
    res = service.embed(["Hello world", "Testing embedding service lazy load."])
    elapsed = time.time() - start
    print(f"[Worker {worker_id}] Finished in {elapsed:.2f} seconds. Got {len(res.embeddings)} vectors.")
    results[worker_id] = elapsed

def main():
    print("=" * 60)
    print("EMBEDDING SERVICE BENCHMARK")
    print("=" * 60)

    # First request: simulating 3 simultaneous uploads
    print("\n--- SIMULATING SIMULTANEOUS FIRST REQUESTS ---")
    threads = []
    results_first = {}
    
    overall_start = time.time()
    for i in range(3):
        t = threading.Thread(target=run_embedding, args=(i, results_first))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    overall_elapsed = time.time() - overall_start
    print(f"\nAll simultaneous first requests completed in {overall_elapsed:.2f} seconds.")
    
    # Second request: single upload after model is loaded
    print("\n--- SECOND REQUEST (CACHED MODEL) ---")
    results_second = {}
    run_embedding(99, results_second)
    
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print("Simultaneous First Requests:")
    for w_id, duration in results_first.items():
        print(f"  Worker {w_id}: {duration:.2f} seconds")
        
    print("\nSecond Request (Cached):")
    print(f"  Worker 99: {results_second[99]:.2f} seconds")
    print("=" * 60)

if __name__ == "__main__":
    main()
