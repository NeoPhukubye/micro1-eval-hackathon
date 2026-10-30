import os
import subprocess
import json
import time
from openai import OpenAI  # Or Anthropic SDK

def run_trial(model_name):
    # 1. Query LLM
    client = OpenAI()
    prompt = open("tasks/task_1_token_bucket.json").read()
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )
    code = response.choices[0].message.content

    # Extract Java code block
    java_code = code.split("```java")[1].split("```")[0]
    with open("src/main/java/com/eval/ratelimiter/TokenBucketRateLimiter.java", "w") as f:
        f.write(java_code)

    # 2. Compile Code
    compile_res = subprocess.run(["mvn", "clean", "compile"], capture_output=True, text=True)
    if compile_res.returncode != 0:
        return "FAIL_COMPILATION", compile_res.stderr

    # 3. Run Concurrency Grader
    grade_res = subprocess.run(
        ["java", "-cp", "target/classes", "com.eval.grader.ConcurrencyGrader"], 
        capture_output=True, 
        text=True
    )
    
    if grade_res.returncode == 0:
        return "PASS", grade_res.stdout
    else:
        return "FAIL_CONCURRENCY_BUG", grade_res.stderr

if __name__ == "__main__":
    models = ["gpt-4o", "claude-3-5-sonnet"]
    results = {}
    for model in models:
        status, log = run_trial(model)
        results[model] = status
        print(f"Model {model}: {status}")
