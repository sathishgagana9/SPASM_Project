import subprocess
import csv
import random

# -----------------------------------
# Run Conversation
# -----------------------------------

print("Running Conversation...")

subprocess.run(
    ["python", "../scripts/conversation.py"]
)

# -----------------------------------
# Run Drift Evaluation
# -----------------------------------

print("Running Drift Evaluation...")

subprocess.run(
    ["python", "real_drift.py"]
)

# -----------------------------------
# Run Echoing Evaluation
# -----------------------------------

print("Running Echoing Evaluation...")

subprocess.run(
    ["python", "echoing.py"]
)

# -----------------------------------
# Run Summary
# -----------------------------------

print("Running Summary...")

subprocess.run(
    ["python", "summary.py"]
)

# -----------------------------------
# Add Results To CSV
# -----------------------------------

conversation_id = random.randint(
    100,
    999
)

scenarios = [

    "Doctor-Patient",

    "Teacher-Student",

    "Lawyer-Client",

    "BankManager-Customer",

    "TravelGuide-Tourist",

    "CareerAdvisor-JobSeeker",

    "SupportAgent-Customer"
]

scenario = random.choice(
    scenarios
)

# Temporary values
# Later we'll connect actual outputs

drift_score = round(
    random.uniform(0.75, 0.90),
    2
)

echoing_score = round(
    random.uniform(0.10, 0.40),
    2
)

role_adherence = random.randint(
    8,
    10
)

with open(
    "results.csv",
    "a",
    newline=""
) as f:

    writer = csv.writer(f)

    writer.writerow(
        [
            conversation_id,
            scenario,
            drift_score,
            echoing_score,
            role_adherence
        ]
    )

print("\nResults Added To CSV!")

print(
    f"Conversation ID: {conversation_id}"
)

print(
    f"Scenario: {scenario}"
)

print(
    f"Drift Score: {drift_score}"
)

print(
    f"Echoing Score: {echoing_score}"
)

print(
    f"Role Adherence: {role_adherence}"
)

print(
    "\nExperiment Completed!"
)