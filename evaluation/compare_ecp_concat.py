import pandas as pd

ecp = pd.read_csv(
    "ecp_results.csv"
)

concat = pd.read_csv(
    "concat_results.csv"
)

print("\nECP RESULTS")
print("-" * 30)

print(
    "Average Drift:",
    ecp["drift_score"].mean()
)

print(
    "Average Echoing:",
    ecp["echoing_score"].mean()
)

print(
    "Average Role:",
    ecp["role_adherence"].mean()
)

print("\nCONCAT RESULTS")
print("-" * 30)

print(
    "Average Drift:",
    concat["drift_score"].mean()
)

print(
    "Average Echoing:",
    concat["echoing_score"].mean()
)

print(
    "Average Role:",
    concat["role_adherence"].mean()
)