import os

# -------------------------
# Find Latest Conversation
# -------------------------

output_folder = "../output"

files = [
    f for f in os.listdir(output_folder)
    if f.startswith("conversation_")
    and f.endswith(".txt")
]

latest_file = max(
    files,
    key=lambda x: os.path.getctime(
        os.path.join(output_folder, x)
    )
)

file_path = os.path.join(
    output_folder,
    latest_file
)

print("Evaluating:", latest_file)

# -------------------------
# Read Conversation
# -------------------------

with open(
    file_path,
    "r",
    encoding="utf-8"
) as f:

    conversation = f.read()

# -------------------------
# Extract Messages
# -------------------------

lines = []

for line in conversation.split("\n"):

    if ":" in line:

        parts = line.split(":", 1)

        message = parts[1].strip()

        if message:

            lines.append(message)

# -------------------------
# Echoing Calculation
# -------------------------

scores = []

for i in range(len(lines) - 1):

    msg1 = set(
        lines[i].lower().split()
    )

    msg2 = set(
        lines[i + 1].lower().split()
    )

    overlap = msg1.intersection(msg2)

    score = len(overlap) / max(
        len(msg2),
        1
    )

    scores.append(score)

# -------------------------
# Average Echoing
# -------------------------

if scores:

    avg_echoing = sum(scores) / len(scores)

else:

    avg_echoing = 0

print(
    "Average Echoing Score:",
    round(avg_echoing, 3)
)