import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("results.csv")

# Drift Graph

plt.figure()

plt.plot(
    df["conversation_id"],
    df["drift_score"],
    marker="o"
)

plt.title("Drift Score")

plt.xlabel("Conversation ID")

plt.ylabel("Drift Score")

plt.grid(True)

plt.savefig(
    "drift_graph.png"
)

plt.close()

# Echoing Graph

plt.figure()

plt.plot(
    df["conversation_id"],
    df["echoing_score"],
    marker="o"
)

plt.title("Echoing Score")

plt.xlabel("Conversation ID")

plt.ylabel("Echoing Score")

plt.grid(True)

plt.savefig(
    "echoing_graph.png"
)

plt.close()

# Role Adherence Graph

plt.figure()

plt.plot(
    df["conversation_id"],
    df["role_adherence"],
    marker="o"
)

plt.title("Role Adherence")

plt.xlabel("Conversation ID")

plt.ylabel("Role Score")

plt.grid(True)

plt.savefig(
    "role_graph.png"
)

plt.close()

print("Graphs Generated Successfully!")