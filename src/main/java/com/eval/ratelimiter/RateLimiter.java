package com.eval.ratelimiter;

public interface RateLimiter {
    boolean tryConsume(long tokens);
}
