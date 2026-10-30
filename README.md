# Eval Name: `java-concurrency-ratelimiter-eval`

### 1. Domain & Failure Hypothesis

* **The Domain:** High-throughput Java backend systems (Spring Boot, Netty, Microservices).
* **Where AI Models Fail:** AI models frequently write Java code that *looks* correct for single-threaded or low-concurrency execution but fails catastrophically under high concurrent load due to race conditions, non-atomic operations, subtle deadlocks, or improper memory visibility (`volatile` vs. `AtomicReference`).
* **Why It Matters:** In financial systems, microservices, and API gateways, unhandled concurrency edge cases lead to double-spending, resource starvation, thread leakage, and security bypasses.

### 2. The Task

Implement a thread-safe token bucket rate limiter in Java inside a class named `TokenBucketRateLimiter` implementing the provided `RateLimiter` interface.

**Requirements:**
1. Constructor: `TokenBucketRateLimiter(long maxCapacity, long refillRatePerSecond)`
2. Method: `boolean tryConsume(long tokens)`
   - Returns `true` if `tokens` were successfully consumed, `false` otherwise.
   - Token replenishment must reflect elapsed time continuously (lock-free or fine-grained locking preferred).

**Strict Constraints:**
- Must support high-concurrency access across hundreds of threads without blocking or causing lock contention deadlocks.
- Must **never** allow available tokens to exceed `maxCapacity` or drop below `0`.
- Must not use coarse-grained `synchronized` methods that wrap the entire `tryConsume` operation, as this chokes throughput.
- Must handle clock skew or nanoTime overflow safely.

### Failure Patterns Caught
1. **The Read-Then-Write Anti-Pattern:** `if (tokens >= requested) { tokens -= requested; return true; }` without atomic locking approves too many requests.
2. **Coarse-grained Lock Bottlenecks:** Wrapping entire function in `synchronized` passes safety but fails scalability.
3. **Double-Checked Locking Flaws:** Custom non-blocking algorithms without `AtomicReference` cause lost updates.
