#!/usr/bin/env python3
import os
import json
import subprocess
import time
from pathlib import Path
from openai import OpenAI

MODELS = ["gpt-4o", "claude-3-5-sonnet", "llama-3.1-70b"]
TASKS = ["task_1_token_bucket.json", "task_2_bounded_queue.json", "task_3_distributed_lock.json"]
TRIALS = 3  # 3 trials per task per model = 27 total runs

def run_single_trial(model_name, task_file, trial_num):
    print(f"Executing {model_name} | {task_file} | Trial {trial_num}...")
    
    # 1. Load Task
    with open(f"tasks/{task_file}") as f:
        task_data = json.load(f)
        
    # 2. Query LLM
    client = OpenAI()
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": task_data["prompt"]}],
        temperature=0.2
    )
    raw_output = response.choices[0].message.content

    # Save Log File in transcripts/
    log_filename = f"transcripts/{model_name}_{task_data['task_id']}_trial{trial_num}.log"
    os.makedirs("transcripts", exist_ok=True)
    with open(log_filename, "w") as f:
        f.write(raw_output)

    # 3. Extract Java Code
    try:
        java_code = raw_output.split("```java")[1].split("```")[0]
    except IndexError:
        return "FAIL_FORMATTING", 0

    # Write Java file to build directory
    target_path = Path("src/main/java/com/eval/ratelimiter/TokenBucketRateLimiter.java")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(java_code)

    # 4. Compile Maven Project
    compile_proc = subprocess.run(["mvn", "clean", "test-compile"], capture_output=True, text=True)
    if compile_proc.returncode != 0:
        return "FAIL_COMPILATION", 0

    # 5. Run Concurrency Grader
    run_proc = subprocess.run(
        ["java", "-cp", "target/classes:target/test-classes", "com.eval.grader.ConcurrencyGrader"],
        capture_output=True,
        text=True
    )

    # Parse Results
    for line in run_proc.stdout.splitlines():
        if "JSON_RESULT:" in line:
            res_data = json.loads(line.replace("JSON_RESULT:", "").strip())
            return res_data["status"], res_data.get("duration_ms", 0)

    return "FAIL_UNKNOWN", 0

def main():
    summary_results = []

    for model in MODELS:
        for task in TASKS:
            passes = 0
            durations = []
            
            for t in range(1, TRIALS + 1):
                status, duration = run_single_trial(model, task, t)
                if status == "PASS":
                    passes += 1
                durations.append(duration)

            pass_at_k = 1.0 if passes > 0 else 0.0
            pass_pow_k = 1.0 if passes == TRIALS else 0.0
            pass_rate = (passes / TRIALS) * 100

            summary_results.append({
                "model": model,
                "task": task,
                "pass_rate": f"{pass_rate:.1f}%",
                "pass_at_k": pass_at_k,
                "pass_pow_k": pass_pow_k,
                "trials_passed": f"{passes}/{TRIALS}"
            })

    # Save to summary.csv
    os.makedirs("results", exist_ok=True)
    with open("results/summary.csv", "w") as f:
        f.write("model,task,pass_rate,pass_at_k,pass_pow_k,trials_passed\n")
        for r in summary_results:
            f.write(f"{r['model']},{r['task']},{r['pass_rate']},{r['pass_at_k']},{r['pass_pow_k']},{r['trials_passed']}\n")

    print("\nSummary Results Saved to results/summary.csv")

if __name__ == "__main__":
    main()
