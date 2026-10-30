package com.eval.grader;

import com.eval.ratelimiter.TokenBucketRateLimiter;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class ConcurrencyGrader {

    public static void main(String[] args) throws Exception {
        int threads = 100;
        int requestsPerThread = 1000;
        long maxCapacity = 500;
        long refillRate = 100; // tokens/sec

        TokenBucketRateLimiter limiter = new TokenBucketRateLimiter(maxCapacity, refillRate);

        ExecutorService executor = Executors.newFixedThreadPool(threads);
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch endLatch = new CountDownLatch(threads);
        AtomicInteger totalApproved = new AtomicInteger(0);

        for (int i = 0; i < threads; i++) {
            executor.submit(() -> {
                try {
                    startLatch.await(); // Synchronize all 100 threads to fire simultaneously
                    for (int j = 0; j < requestsPerThread; j++) {
                        if (limiter.tryConsume(1)) {
                            totalApproved.incrementAndGet();
                        }
                    }
                } catch (Exception e) {
                    Thread.currentThread().interrupt();
                } finally {
                    endLatch.countDown();
                }
            });
        }

        long startTime = System.currentTimeMillis();
        startLatch.countDown(); // Fire!
        
        // Deadlock & Hang Safeguard (Max 5 Seconds)
        boolean completed = endLatch.await(5, TimeUnit.SECONDS);
        long duration = System.currentTimeMillis() - startTime;
        executor.shutdownNow();

        if (!completed) {
            System.out.println("JSON_RESULT: {\"status\": \"DEADLOCK_TIMEOUT\", \"approved\": " + totalApproved.get() + ", \"duration_ms\": " + duration + "}");
            System.exit(1);
        }

        // Throughput Bottleneck Check (Must finish < 500ms)
        if (duration > 500) {
            System.out.println("JSON_RESULT: {\"status\": \"FAIL_THROUGHPUT_BOTTLENECK\", \"approved\": " + totalApproved.get() + ", \"duration_ms\": " + duration + "}");
            System.exit(1);
        }

        // Race Condition Check
        if (totalApproved.get() > (maxCapacity + 20) || totalApproved.get() < maxCapacity) {
            System.out.println("JSON_RESULT: {\"status\": \"FAIL_RACE_CONDITION\", \"approved\": " + totalApproved.get() + ", \"duration_ms\": " + duration + "}");
            System.exit(1);
        }

        System.out.println("JSON_RESULT: {\"status\": \"PASS\", \"approved\": " + totalApproved.get() + ", \"duration_ms\": " + duration + "}");
        System.exit(0);
    }
}
