import json

from llm import generate

# ----------------------------------
# Read Conversation
# ----------------------------------

with open(
    "../output/conversation_583.txt",
    "r",
    encoding="utf-8"
) as f:

    conversation = f.read()

# ----------------------------------
# Probe Questions
# ----------------------------------

questions = [

    "Who are you?",

    "What is your occupation?",

    "How do you feel right now?",

    "What problem are you facing?",

    "What are your goals?"
]

answers = {}

# ----------------------------------
# Ask Ollama
# ----------------------------------

for question in questions:

    prompt = f"""
Conversation:

{conversation}

Based ONLY on the final state of the agent after the conversation.

Answer this question briefly.

Question:
{question}
"""

    try:

        response = generate(prompt)

        answers[question] = response.strip()

    except Exception as e:

        print(e)

        answers[question] = "N/A"

# ----------------------------------
# Save Results
# ----------------------------------

with open(
    "final.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        answers,
        f,
        indent=4
    )

print("Final Persona State Saved")