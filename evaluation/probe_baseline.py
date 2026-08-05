import os
import sys

CURRENT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

SCRIPTS_DIR = os.path.join(
    CURRENT_DIR,
    "..",
    "scripts"
)

sys.path.append(
    os.path.abspath(SCRIPTS_DIR)
)

from persona_schema import generate_persona
from persona_validator import validate_persona
from drift_probe import get_probe_questions

import json

persona = generate_persona()

while not validate_persona(persona):
    persona = generate_persona()

baseline_answers = {

    "Who are you?":
        f"I am a {persona['occupation']}.",

    "What is your occupation?":
        persona["occupation"],

    "How do you feel right now?":
        persona["emotion"],

    "What problem are you facing?":
        persona["context"],

    "What are your goals?":
        f"To handle {persona['context']} successfully."
}

with open(
    "baseline.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        baseline_answers,
        f,
        indent=4
    )

print("Baseline Answers Saved")

print("\nBaseline State:\n")

for question, answer in baseline_answers.items():

    print(question)
    print(answer)
    print()