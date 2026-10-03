import pandas as pd

# Example results
ecp_results = pd.read_csv("ecp_results.csv")
concat_results = pd.read_csv("concat_results.csv")

print("\nECP RESULTS")
print("-" * 30)

print(
    "Average Drift:",
    ecp_results["drift_score"].mean()
)

print(
    "Average Echoing:",
    ecp_results["echoing_score"].mean()
)

print(
    "Average Role:",
    ecp_results["role_adherence"].mean()
)

print("\nCONCAT RESULTS")
print("-" * 30)

print(
    "Average Drift:",
    concat_results["drift_score"].mean()
)

print(
    "Average Echoing:",
    concat_results["echoing_score"].mean()
)

print(
    "Average Role:",
    concat_results["role_adherence"].mean()
)