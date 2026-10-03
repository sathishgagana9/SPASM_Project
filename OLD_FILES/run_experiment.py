import subprocess

print("=" * 50)
print("RUNNING SPASM EXPERIMENT")
print("=" * 50)

# ----------------------------------
# Conversation Generation
# ----------------------------------

print("\nRunning Conversation...")

subprocess.run([
    "python",
    "scripts/conversation.py"
])

# ----------------------------------
# Echoing Evaluation
# ----------------------------------

print("\nRunning Echoing Evaluation...")

subprocess.run([
    "python",
    "evaluation/echoing_file.py"
])

# ----------------------------------
# Drift Evaluation
# ----------------------------------

print("\nRunning Drift Evaluation...")

subprocess.run([
    "python",
    "evaluation/real_drift_file.py"
])

# ----------------------------------
# Generate Probe Baseline
# ----------------------------------

print("\nGenerating Baseline...")

subprocess.run([
    "python",
    "evaluation/probe_baseline.py"
])

# ----------------------------------
# Generate Probe Final
# ----------------------------------

print("\nGenerating Final State...")

subprocess.run([
    "python",
    "evaluation/probe_final.py"
])

# ----------------------------------
# Probe Drift Evaluation
# ----------------------------------

print("\nRunning Probe Drift Evaluation...")

subprocess.run([
    "python",
    "evaluation/probe_drift_score.py"
])

# ----------------------------------
# Role Adherence Evaluation
# ----------------------------------

print("\nRunning Role Adherence Evaluation...")

subprocess.run([
    "python",
    "evaluation/role_adherence.py"
])

# ----------------------------------
# Summary
# ----------------------------------

print("\nRunning Summary...")

subprocess.run([
    "python",
    "evaluation/summary.py"
])

print("\n")
print("=" * 50)
print("EXPERIMENT COMPLETE")
print("=" * 50)