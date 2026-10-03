import pandas as pd

df = pd.read_csv(
    "results.csv"
)

print(
    "Average Drift:",
    df["drift_score"].mean()
)

print(
    "Average Echoing:",
    df["echoing_score"].mean()
)

print(
    "Average Role Adherence:",
    df["role_adherence"].mean()
)