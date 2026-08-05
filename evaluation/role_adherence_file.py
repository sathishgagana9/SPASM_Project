import os
import re

from llm import generate

# ----------------------------------
# Find Latest Conversation
# ----------------------------------

output_folder = "../output"

files = [

    f for f in os.listdir(output_folder)

    if f.startswith("conversation_")
    and f.endswith(".txt")
]

latest_file = max(

    files,

    key=lambda x:
    os.path.getctime(
        os.path.join(
            output_folder,
            x
        )
    )
)

FILE_PATH = os.path.join(
    output_folder,
    latest_file
)

print(
    "Evaluating:",
    latest_file
)

# ----------------------------------
# Generic Role
# ----------------------------------

ROLE = "Professional Assistant"

# ----------------------------------
# Read Conversation
# ----------------------------------

with open(
    FILE_PATH,
    "r",
    encoding="utf-8"
) as f:

    conversation = f.read()

# ----------------------------------
# Extract Agent1 Responses
# ----------------------------------

responses = re.findall(
    r"Agent1 :(.*?)(?=Agent2 :|$)",
    conversation,
    re.DOTALL
)

scores = []

# ----------------------------------
# Score Responses
# ----------------------------------

for response in responses:

    prompt = f"""
Role:

{ROLE}

Response:

{response}

Rate how well this response follows the role.

Give ONLY a number from 1 to 10.

Do not explain.
"""

    try:

        result = generate(prompt).strip()

        match = re.search(r"\d+(\.\d+)?", result)

        if match:

            score = float(match.group())

            scores.append(score)

            print(
                f"Response Score: {score}"
            )

        else:

            print(
                "Invalid response:",
                result
            )

    except Exception as e:

        print(
            "Skipped:",
            e
        )

# ----------------------------------
# Average Role Adherence
# ----------------------------------

if scores:

    average_score = (
        sum(scores)
        /
        len(scores)
    )

    print(
        "\nAverage Role Adherence:",
        round(
            average_score,
            2
        )
    )

else:

    print(
        "\nAverage Role Adherence: 0"
    )