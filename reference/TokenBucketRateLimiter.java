package com.eval.ratelimiter;

import java.util.concurrent.atomic.AtomicReference;

public class TokenBucketRateLimiter implements RateLimiter {

    private final long maxCapacity;
    private final long refillRatePerSecond; // Tokens per second
    private final AtomicReference<State> state;

    private static class State {
        final double tokens;
        final long lastRefillNanos;

        State(double tokens, long lastRefillNanos) {
            this.tokens = tokens;
            this.lastRefillNanos = lastRefillNanos;
        }
    }

    public TokenBucketRateLimiter(long maxCapacity, long refillRatePerSecond) {
        this.maxCapacity = maxCapacity;
        this.refillRatePerSecond = refillRatePerSecond;
        this.state = new AtomicReference<>(new State(maxCapacity, System.nanoTime()));
    }

    public boolean tryConsume(long tokensRequested) {
        if (tokensRequested <= 0) {
            throw new IllegalArgumentException("Tokens requested must be positive");
        }

        while (true) {
            long now = System.nanoTime();
            State current = state.get();
            
            // 1. Calculate refilled tokens based on elapsed time
            long elapsedNanos = Math.max(0, now - current.lastRefillNanos);
            double tokensToAdd = (elapsedNanos / 1_000_000_000.0) * refillRatePerSecond;
            double newTokens = Math.min((double) maxCapacity, current.tokens + tokensToAdd);

            // 2. Check availability
            if (newTokens < tokensRequested) {
                return false;
            }

            // 3. Atomically update state using CAS (Compare-And-Swap)
            State updated = new State(newTokens - tokensRequested, now);
            if (state.compareAndSet(current, updated)) {
                return true;
            }
            // CAS failed due to concurrent modification -> loop retries safely
        }
    }
}
