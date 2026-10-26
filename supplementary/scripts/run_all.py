import sys
import os
import subprocess

def run_command_checked(cmd):
    print("\n" + "=" * 70)
    print(f"RUNNING: {cmd}")
    print("=" * 70)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.abspath(os.path.dirname(__file__))
    ret = subprocess.run([sys.executable] + cmd.split()[1:], env=env)
    if ret.returncode != 0:
        print(f"[ERROR] Step {cmd} failed with return code {ret.returncode}")
        sys.exit(ret.returncode)

def main():
    print("=" * 70)
    print("ONE-COMMAND REPRODUCTION PIPELINE: CCAF PROJECT")
    print("=" * 70)

    # 1. Benchmark S3 comparison
    run_command_checked("python src/experiments/run_s3_benchmark.py")

    # 2. Monte Carlo campaign (S1, S3, S5, S6)
    run_command_checked("python src/experiments/run_monte_carlo.py")

    # 3. Ablation studies
    run_command_checked("python src/experiments/run_ablations.py")

    # 4. Real-world biomedical validation (S7)
    run_command_checked("python src/experiments/run_s7_benchmark.py")

    # 5. Real-world Aachen Impulse Response (AIR) AEC benchmark
    run_command_checked("python src/experiments/run_air_benchmark.py")

    print("\n" + "=" * 70)
    print("[SUCCESS] All simulations, benchmarks, and ablations reproduced.")
    print("All generated plots and tables are available in the 'results/' directory.")
    print("=" * 70)

if __name__ == "__main__":
    main()
