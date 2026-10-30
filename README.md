# Java Concurrency & Lock-Free Data Structures Evaluation Benchmark

## What It Tests
This benchmark evaluates the capability of frontier AI models (GPT-4o, Claude 3.5 Sonnet, Llama 3.1) to generate thread-safe, lock-free, and deadlock-free Java concurrency components under heavy concurrent thread stress (100+ threads, 100,000 requests).

## Why It Matters
Modern microservices and API gateways rely on lock-free algorithms (`AtomicReference`, CAS loops, ring buffers) for ultra-low latency. AI models frequently write code that passes basic single-threaded unit tests but fails catastrophically under high concurrent load—causing race condition over-allocations, throughput chokes (`synchronized` methods), or thread deadlocks.

## Benchmark Tasks
1. **`task_1_token_bucket`**: Lock-free Token Bucket Rate Limiter via `AtomicReference` and CAS loops.
2. **`task_2_bounded_queue`**: Multi-Producer Single-Consumer (MPSC) lock-free bounded queue using `AtomicReferenceArray`.
3. **`task_3_distributed_lock`**: Deterministic hierarchical lock manager to prevent opposing-thread deadlocks.

## Evaluation Metrics & Results

| Model | Task | Pass Rate | pass@k | pass^k | Primary Failure Mode |
| :--- | :--- | :---: | :---: | :---: | :--- |
| GPT-4o | Token Bucket | 33.3% | 1.0 | 0.0 | Race Condition (Over-allocation) |
| Claude 3.5 Sonnet | Token Bucket | 66.7% | 1.0 | 0.0 | Throughput Bottleneck (`synchronized`) |
| Llama 3.1 70B | Token Bucket | 0.0% | 0.0 | 0.0 | Deadlock Timeout |

- **`pass@k`**: Succeeded in at least 1 of 3 trials.
- **`pass^k`**: Succeeded in 100% of trials consistently.

## Setup and Reproduction
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure Environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 3. Run Benchmark Harness
python run_eval.py
```

## Failure Analysis & Key Insights

1. **Read-Then-Write Anti-Pattern**: Models frequently perform read and write operations across separate statements without atomic state wrapping, causing high thread race conditions.
2. **Coarse-Grained Fallbacks**: When prompted for thread safety, models default to `synchronized` methods, which chokes throughput under concurrent load (>500ms duration).
