# Eval Name: `java-concurrency-ratelimiter-eval`

### 1. Domain & Failure Hypothesis

* **The Domain:** High-throughput Java backend systems (Spring Boot, Netty, Microservices).
* **Where AI Models Fail:** AI models frequently write Java code that *looks* correct for single-threaded or low-concurrency execution but fails catastrophically under high concurrent load due to race conditions, non-atomic operations, subtle deadlocks, or improper memory visibility (`volatile` vs. `AtomicReference`).
* **Why It Matters:** In financial systems, microservices, and API gateways, unhandled concurrency edge cases lead to double-spending, resource starvation, thread leakage, and security bypasses.

### 2. Comprehensive Multi-Dimensional Benchmark Suite

Rather than a single isolated test, this suite evaluates three hard concurrency edge cases:

1. **Task 1: Token Bucket Rate Limiter (Lock-Free / CAS Loop)** - Non-blocking rate limiter; fails on coarse-grained `synchronized` (throughput choke) or non-atomic state updates (over-allocation).
2. **Task 2: Lock-Free Bounded Queue (ABA Problem & Pointer Race)** - High-performance lock-free ring buffer using `AtomicReferenceArray`; misses memory visibility/cache issues causing silent corruption/null drops under MPSC.
3. **Task 3: Dynamic Distributed Lock Manager (Deadlock via Out-of-Order Acquisition)** - Hierarchical lock acquisition across multiple resource IDs; fails to enforce deterministic lock ordering causing catastrophic deadlocks under contention.

### 3. Grading Dimensions

Our grader evaluates three strict dimensions:

- **Correctness / Race Condition Checks:** Zero over-allocation under concurrent load.
- **Performance / Throughput Threshold:** Must process ≥ 100,000 concurrent requests in under 500 ms (rejects `synchronized` bottlenecks).
- **Deadlock Timeout Safeguard:** Enforces a strict 5-second runtime ceiling using `ExecutorService.awaitTermination()`.

### 4. Statistical Reliability

Runs **5 trials per model per task** and reports both **`pass@k`** (passed at least once) and **`pass^k`** (passed consistently every trial).

### Failure Patterns Caught
1. **The Read-Then-Write Anti-Pattern:** `if (tokens >= requested) { tokens -= requested; return true; }` without atomic locking approves too many requests.
2. **Coarse-grained Lock Bottlenecks:** Wrapping entire function in `synchronized` passes safety but fails scalability and duration thresholds.
3. **Double-Checked Locking Flaws:** Custom non-blocking algorithms without `AtomicReference` cause lost updates and race conditions.
