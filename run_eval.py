#!/usr/bin/env python3
import os
import json
import subprocess
import time
from pathlib import Path
from openai import OpenAI

MODELS = ["gpt-4o", "claude-3-5-sonnet", "llama-3.1-70b"]
TRIALS = 5

def run_evaluation(model_name, trial_idx):
    print(f"Running {model_name} - Trial {trial_idx + 1}/{TRIALS}...")
    
    # 1. Read Task Prompt
    with open("tasks/task_1_token_bucket.json") as f:
        task_data = json.load(f)

    # 2. Query LLM
    client = OpenAI()
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": task_data["prompt"]}],
        temperature=0.2
    )
    raw_output = response.choices[0].message.content

    # Save raw transcript
    transcript_path = f"transcripts/{model_name}_trial_{trial_idx + 1}.log"
    with open(transcript_path, "w") as f:
        f.write(raw_output)

    # 3. Extract and Write Java File
    try:
        java_code = raw_output.split("```java")[1].split("```")[0]
    except IndexError:
        return "FAIL_FORMATTING", 0

    target_file = Path("src/main/java/com/eval/ratelimiter/TokenBucketRateLimiter.java")
    target_file.write_text(java_code)

    # 4. Compile Maven Project
    compile_proc = subprocess.run(["mvn", "clean", "test-compile"], capture_output=True, text=True)
    if compile_proc.returncode != 0:
        return "FAIL_COMPILATION", 0

    # 5. Execute Concurrency Grader
    run_proc = subprocess.run(
        ["java", "-cp", "target/classes:target/test-classes", "com.eval.grader.ConcurrencyGrader"],
        capture_output=True,
        text=True
    )

    # Parse JSON stdout output
    for line in run_proc.stdout.splitlines():
        if "JSON_RESULT:" in line:
            res_data = json.loads(line.replace("JSON_RESULT:", "").strip())
            return res_data["status"], res_data["duration_ms"]

    return "FAIL_UNKNOWN", 0

def main():
    results_summary = []
    
    for model in MODELS:
        passes = 0
        trials_data = []
        
        for t in range(TRIALS):
            status, duration = run_evaluation(model, t)
            if status == "PASS":
                passes += 1
            trials_data.append({"trial": t + 1, "status": status, "duration_ms": duration})

        pass_at_k = 1.0 if passes > 0 else 0.0
        pass_pow_k = 1.0 if passes == TRIALS else 0.0

        results_summary.append({
            "model": model,
            "pass_rate": f"{(passes / TRIALS) * 100:.1f}%",
            "pass_at_k": pass_at_k,
            "pass_pow_k": pass_pow_k,
            "trials": trials_data
        })

    # Save Output CSV Summary
    with open("results/summary.csv", "w") as f:
        f.write("model,pass_rate,pass_at_k,pass_pow_k\n")
        for row in results_summary:
            f.write(f"{row['model']},{row['pass_rate']},{row['pass_at_k']},{row['pass_pow_k']}\n")

    print("\n=== EVALUATION COMPLETE ===")
    print(json.dumps(results_summary, indent=2))

if __name__ == "__main__":
    main()
