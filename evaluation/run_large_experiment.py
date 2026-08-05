import subprocess
import pandas as pd
import re

results = []

NUM_PERSONAS = 5
RUNS_PER_PERSONA = 3

for persona_id in range(1, NUM_PERSONAS + 1):

    print(f"\nRunning Persona {persona_id}")

    for run in range(1, RUNS_PER_PERSONA + 1):

        print(f"  Conversation {run}")

        # ----------------------------
        # Generate Conversation
        # ----------------------------

        subprocess.run(
            [
                "python",
                "../scripts/conversation.py"
            ]
        )

        # ----------------------------
        # Drift
        # ----------------------------

        drift_output = subprocess.check_output(
            [
                "python",
                "real_drift_file.py"
            ]
        ).decode()

        drift_match = re.search(
            r"Drift Score:\s*([0-9.]+)",
            drift_output
        )

        drift_score = (
            float(drift_match.group(1))
            if drift_match
            else 0
        )

        # ----------------------------
        # Echoing
        # ----------------------------

        echo_output = subprocess.check_output(
            [
                "python",
                "echoing_file.py"
            ]
        ).decode()

        echo_match = re.search(
            r"Average Echoing Score:\s*([0-9.]+)",
            echo_output
        )

        echoing_score = (
            float(echo_match.group(1))
            if echo_match
            else 0
        )

        # ----------------------------
        # Role Adherence
        # ----------------------------

        role_output = subprocess.check_output(
            [
                "python",
                "role_adherence_file.py"
            ]
        ).decode()

        role_match = re.search(
            r"Average Role Adherence:\s*([0-9.]+)",
            role_output
        )

        role_score = (
            float(role_match.group(1))
            if role_match
            else 0
        )

        results.append({

            "persona_id":
                persona_id,

            "conversation_id":
                run,

            "drift_score":
                drift_score,

            "echoing_score":
                echoing_score,

            "role_adherence":
                role_score
        })

# ----------------------------
# Save Results
# ----------------------------

df = pd.DataFrame(results)

df.to_csv(
    "large_experiment_results.csv",
    index=False
)

print("\nExperiment Complete")

print(
    "\nAverage Drift:",
    round(
        df["drift_score"].mean(),
        4
    )
)

print(
    "Average Echoing:",
    round(
        df["echoing_score"].mean(),
        4
    )
)

print(
    "Average Role:",
    round(
        df["role_adherence"].mean(),
        4
    )
)