package com.eval.grader;

import com.eval.ratelimiter.TokenBucketRateLimiter;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class ConcurrencyGrader {

    public static void main(String[] args) throws InterruptedException {
        int threads = 100;
        int requestsPerThread = 1000;
        long maxCapacity = 500;
        long refillRate = 100; // 100 tokens/sec

        TokenBucketRateLimiter limiter = new TokenBucketRateLimiter(maxCapacity, refillRate);

        ExecutorService executor = Executors.newFixedThreadPool(threads);
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch endLatch = new CountDownLatch(threads);
        AtomicInteger totalApproved = new AtomicInteger(0);

        for (int i = 0; i < threads; i++) {
            executor.submit(() -> {
                try {
                    startLatch.await(); // Wait for all threads to start simultaneously
                    for (int j = 0; j < requestsPerThread; j++) {
                        if (limiter.tryConsume(1)) {
                            totalApproved.incrementAndGet();
                        }
                    }
                } catch (Exception e) {
                    e.printStackTrace();
                } finally {
                    endLatch.countDown();
                }
            });
        }

        // Fire all 100 threads at the exact same instant
        long startTime = System.currentTimeMillis();
        startLatch.countDown();
        endLatch.await();
        long duration = System.currentTimeMillis() - startTime;

        executor.shutdown();

        // VALIDATION LOGIC
        // Initial tokens = 500. Duration ~ 0.1s -> max allowed strictly around 500-510 tokens.
        int totalRequests = threads * requestsPerThread; // 100,000 requests
        System.out.println("Total Requests: " + totalRequests);
        System.out.println("Approved Requests: " + totalApproved.get());
        System.out.println("Execution Duration: " + duration + " ms");

        // Failure Check 1: Over-allocation (Race condition bug)
        if (totalApproved.get() > (maxCapacity + 20)) {
            System.err.println("GRADE: FAIL - Race condition detected! Approved " + totalApproved.get() + " tokens (Capacity was " + maxCapacity + ")");
            System.exit(1);
        }

        // Failure Check 2: Under-allocation or Deadlock
        if (totalApproved.get() < maxCapacity) {
            System.err.println("GRADE: FAIL - Lock starvation or inaccurate state tracking.");
            System.exit(1);
        }

        System.out.println("GRADE: PASS - Thread-safe and atomic under high load.");
        System.exit(0);
    }
}
